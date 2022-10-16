import sys
import socket
import random
import sqlite3
import threading
from datetime import datetime

def connect_tcp():
    while True:
        conn, tcp_addr = tcp.accept()
        print("New connection.")
        WelcomeMessage = "********************************\n** Welcome to the BBS server. **\n********************************"
        conn.sendall(WelcomeMessage.encode())
        tcp_read = threading.Thread(target=read_tcp, args=(conn, ))
        tcp_read.start()


def read_tcp(conn):
    while True:
        data = conn.recv(1024)
        data = data.decode().split()
        if data[1] == 'login':
            Login(data, conn)
        elif data[1] == 'logout':
            Logout(data, conn)
        elif data[1] == 'list-user':
            List_user(data, conn)
        elif data[1] == 'create-board':
            Create_board(data, conn)
        elif data[1] == 'create-post':
            Create_post(data, conn)
        elif data[1] == 'list-board':
            List_board(data, conn)
        elif data[1] == 'list-post':
            List_post(data, conn)
        elif data[1] == 'read':
            Read(data, conn)
        elif data[1] == 'delete-post':
            Delete_post(data, conn)
        elif data[1] == 'update-post':
            Update_post(data, conn)
        elif data[1] == 'comment':
            Comment(data, conn)
        elif data[1] == 'exit':
            if len(data) == 2:
                datadb = sqlite3.connect("data.db")
                db = datadb.cursor()
                db.execute(
                    '''DELETE FROM CLIENT WHERE Random_id = ?''', (data[0], ))
                datadb.commit()
                datadb.close()
                conn.close()
                break
            else:
                conn.sendall("Usage: exit".encode())


def read_udp():
    while True:
        data, udp_addr = udp.recvfrom(1024)
        data = data.decode().split()
        if data[1] == 'register':
            Register(data, udp_addr)
        elif data[1] == 'whoami':
            Whoami(data, udp_addr)


def Register(data, udp_addr):
    if len(data) == 5:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT COUNT(Username) FROM USERS WHERE Username = ?''', (data[2],))
        count = db.fetchone()
        if count[0] == 0:
            db.execute('''INSERT INTO USERS (Username , Email , Password) VALUES (? , ? , ?)''',(data[2], data[3], data[4]))
            datadb.commit()
            udp.sendto("Register successfully.".encode(), udp_addr)
        else:
            udp.sendto("Username is already used.".encode(), udp_addr)
        datadb.close()
    else:
        udp.sendto(
            "Usage: register <username> <email> <password>".encode(), udp_addr)


def Login(data, conn):
    if len(data) == 4:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            message = str(data[0]) + ' ' + "Please logout first."
            conn.sendall(message.encode())
        else:
            db.execute('''SELECT Username FROM USERS WHERE Username = ? AND Password = ?''', (data[2], data[3],))
            fetch = db.fetchone()
            if fetch is not None:
                client_name = fetch[0]
                random_id = random.randint(1, 2147483647)
                db.execute('''REPLACE INTO CLIENT (Random_id , Client_name) VALUES (? , ?)''', (random_id, client_name))
                datadb.commit()
                message = str(random_id) + ' ' + \
                    "Welcome, " + client_name + "."
                conn.sendall(message.encode())
            else:
                message = str(data[0]) + " " + "Login failed."
                conn.sendall(message.encode())
        datadb.close()
    else:
        message = str(data[0]) + ' ' + "Usage: login <username> <password>"
        conn.sendall(message.encode())


def Logout(data, conn):
    if len(data) == 2:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            db.execute('''DELETE FROM CLIENT WHERE Random_id = ?''', (data[0], ))
            datadb.commit()
            string = "Bye, " + client_name[0] + "."
            conn.sendall(string.encode())
        else:
            conn.sendall("Please login first.".encode())
        datadb.close()
    else:
        conn.sendall("Usage: logout".encode())


def Whoami(data, udp_addr):
    if len(data) == 2:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        datadb.close()
        if client_name is not None:
            udp.sendto(client_name[0].encode(), udp_addr)
        else:
            udp.sendto("Please login first.".encode(), udp_addr)
    else:
        udp.sendto("Usage: whoami".encode(), udp_addr)


def List_user(data, conn):
    if len(data) == 2:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Username , Email FROM USERS''')
        row = db.fetchall()
        datadb.close()
        string = '{:<10} {:<20}'.format('Name', 'Email')
        for r in row:
            string += '\n' + '{:<10} {:<20}'.format(r[0], r[1])
        conn.sendall(string.encode())
    else:
        conn.sendall("Usage: list-user".encode())


def Create_board(data, conn):
    if len(data) == 3:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            db.execute('''SELECT COUNT(Board_name) FROM BOARD WHERE Board_name = ?''', (data[2],))
            count = db.fetchone()
            if count[0] == 0:
                db.execute('''INSERT INTO BOARD (Board_name , Moderator) VALUES (? , ?)''', (data[2], client_name[0]))
                conn.sendall("Create board successfully.".encode())
            else:
                conn.sendall("Board already exists.".encode())
        else:
            conn.sendall("Please login first.".encode())
    else:
        conn.sendall("Usage: create-board <name>".encode())
    datadb.commit()
    datadb.close()

def Create_post(data, conn):
    lock.acquire()
    global post
    global post_id
    if len(data) >= 7 and data[3] == '--title' and data.index('--content') >= 5:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            db.execute('''SELECT COUNT(Board_name) FROM BOARD WHERE Board_name = ?''', (data[2],))
            count = db.fetchone()
            if count[0] != 0:
                board_name = data[2]
                title = ""
                content = ""
                now = datetime.now()
                time = now.strftime("%m/%d")
                for i in range(data.index('--title') + 1, data.index('--content')):
                    title += data[i] + ' '
                for i in range(data.index('--content') + 1, len(data)):
                    data[i] = data[i].replace('<br>', '\n')
                    content += data[i] + ' '
                
                cur_post = [board_name, str(post_id), title, client_name[0], time, content , []]
                post.append(cur_post)
                post_id += 1
                conn.sendall("Create post successfully.".encode())
            else:
                conn.sendall("Board does not exist.".encode())
        else:
            conn.sendall("Please login first.".encode())
    else:
        conn.sendall("Usage: create-post <board-name> --title <title> --content <content>".encode())
    datadb.close()
    lock.release()

def List_board(data, conn):
    if len(data) == 2:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT BID , Board_name , Moderator FROM BOARD''')
        row = db.fetchall()
        datadb.close()
        string ='{:<8} {:<20} {:<10}'.format('Index', 'Name', 'Moderator')
        for r in row:
            string += '\n' + '{:<8} {:<20} {:<10}'.format(str(r[0]), r[1], r[2])
        conn.sendall(string.encode())
    else:
        conn.sendall("Usage: list-board".encode())

def List_post(data, conn):
    global post
    if len(data) == 3:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT COUNT(Board_name) FROM BOARD WHERE Board_name = ?''', (data[2],))
        count = db.fetchone()
        if count[0] != 0:
            string = '{:<4} {:<20} {:<10} {:<5}'.format('S/N', 'Title', 'Author', 'Date')
            for item in post:
                if item[0] == data[2]:
                    string += '\n' + '{:<4} {:<20} {:<10} {:<5}'.format(item[1], item[2], item[3], item[4])
            conn.sendall(string.encode())
        else:
            conn.sendall("Board does not exist.".encode())
    else:
        conn.sendall("Usage: list-post <board-name>".encode())

def Read(data, conn):
    global post
    global post_id
    if len(data) == 3:
        if int(data[2]) > 0 and int(data[2]) < post_id:
            item = post[int(data[2]) - 1]
            if item[4] != 0:
                string = 'Author: ' + item[3] + '\nTitle: ' + item[2] + '\nDate: ' + item[4] + '\n--\n' + item[5] + '\n--'
                for comment in item[6]:
                    string += '\n' + comment[0] + ': ' + comment[1]
                conn.sendall(string.encode())
            else:
                conn.sendall("Post does not exist.".encode())
        else:
            conn.sendall("Post does not exist.".encode())
    else:
        conn.sendall("Usage: read <post-S/N>".encode())

def Delete_post(data, conn):
    lock.acquire()
    global post
    global post_id
    if len(data) == 3:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            if int(data[2]) > 0 and int(data[2]) < post_id:
                item = post[int(data[2]) - 1]
                if item[4] != 0:
                    if client_name[0] == item[3]:
                        post[int(data[2]) - 1] = [0, 0, 0, 0, 0, 0, []]
                        conn.sendall("Delete successfully.".encode())
                    else:
                        conn.sendall("Not the post owner.".encode())
                else:
                    conn.sendall("Post does not exist.".encode())
            else:
                conn.sendall("Post does not exist.".encode())
        else:
            conn.sendall("Please login first.".encode())
    else:
        conn.sendall("Usage: delete-post <post-S/N>".encode())
    lock.release()

def Update_post(data, conn):
    lock.acquire()
    global post
    global post_id
    if len(data) >= 5 and (data[3] == '--title' or data[3] == '--content'):
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            if int(data[2]) > 0 and int(data[2]) < post_id:
                item = post[int(data[2]) - 1]
                if item[4] != 0:
                    if client_name[0] == item[3]:
                        string = ""
                        for i in range(4, len(data)):
                            data[i] = data[i].replace('<br>', '\n')
                            string += data[i] + ' '
                        if data[3] =='--title':
                            item[2] = string
                        else:
                            item[5] = string
                        conn.sendall("Update successfully.".encode())
                    else:
                        conn.sendall("Not the post owner.".encode())
                else:
                    conn.sendall("Post does not exist.".encode())
            else:
                conn.sendall("Post does not exist.".encode())
        else:
            conn.sendall("Please login first.".encode())
    else:
        conn.sendall("Usage: update-post <post-S/N> --title/content <new>".encode())
    lock.release()

def Comment(data, conn):
    lock.acquire()
    if len(data) >= 4:
        datadb = sqlite3.connect("data.db")
        db = datadb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0],))
        client_name = db.fetchone()
        if client_name is not None:
            if int(data[2]) > 0 and int(data[2]) < post_id:
                item = post[int(data[2]) - 1]
                if item[4] != 0:
                    comment = ""
                    for i in range(3 , len(data)):
                        comment += data[i] + ' '
                    cur_comment = [client_name[0] , comment]
                    item[6].append(cur_comment)
                    conn.sendall("Comment successfully.".encode())
                else:
                    conn.sendall("Post does not exist.".encode())
            else:
                conn.sendall("Post does not exist.".encode())
        else:
            conn.sendall("Please login first.".encode())
    else:
        conn.sendall("Usage: comment <post-S/N> <comment>".encode())
    lock.release()

HOST = "127.0.0.1"
PORT = int(sys.argv[1])

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.bind((HOST, PORT))
tcp.listen(50)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind((HOST, PORT))

datadb = sqlite3.connect("data.db", check_same_thread=False)
db = datadb.cursor()
db.execute('''
CREATE TABLE IF NOT EXISTS USERS(
UID INTEGER PRIMARY KEY AUTOINCREMENT,
Username TEXT NOT NULL UNIQUE,
Email TEXT NOT NULL,
Password TEXT NOT NULL);''')
db.execute('''
CREATE TABLE IF NOT EXISTS CLIENT(
Random_id INTEGER PRIMARY KEY NOT NULL UNIQUE,
Client_name TEXT NOT NULL)''')
db.execute('''
CREATE TABLE IF NOT EXISTS BOARD(
BID INTEGER PRIMARY KEY AUTOINCREMENT,
Board_name TEXT NOT NULL UNIQUE,
Moderator TEXT NOT NULL)''')
datadb.commit()
datadb.close()

post = []
post_id = 1
lock = threading.Lock()

tcp_connect = threading.Thread(target=connect_tcp, args=())
tcp_connect.start()
udp_read = threading.Thread(target=read_udp, args=())
udp_read.start()