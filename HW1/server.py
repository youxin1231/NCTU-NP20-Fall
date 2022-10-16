import sys
import socket
import random
import sqlite3
import threading

def connect_tcp():
    while True:
        conn , tcp_addr = tcp.accept()
        print("New connection.")
        WelcomeMessage = "********************************\n** Welcome to the BBS server. **\n********************************"
        conn.sendall(WelcomeMessage.encode())
        tcp_read = threading.Thread(target=read_tcp , args=(conn , ))
        tcp_read.start()

def read_tcp(conn):
    while True:
        data = conn.recv(1024)
        data = data.decode().split()
        if data[1] == 'login':
            Login(data , conn)
        elif data[1] == 'logout':
            Logout(data , conn)
        elif data[1] == 'list-user':
            List_user(data , conn)
        elif data[1] == 'exit':
            if len(data) == 2:
                userdb = sqlite3.connect("user.db")
                db = userdb.cursor()
                db.execute('''DELETE FROM CLIENT WHERE Random_id = ?''', (data[0] , ))
                userdb.commit()
                userdb.close()
                conn.close()
                break
            else:
                conn.sendall("Usage: exit".encode())

def read_udp():
    while True:
        data , udp_addr = udp.recvfrom(1024)
        data = data.decode().split()
        if data[1] == 'register':
            Register(data , udp_addr)
        elif data[1] == 'whoami':
            Whoami(data , udp_addr)

def Register(data , udp_addr):
    if len(data) == 5:
        userdb = sqlite3.connect("user.db")
        db = userdb.cursor()
        db.execute('''SELECT COUNT(Username) FROM USERS WHERE Username = ?''', (data[2] ,))
        count = db.fetchone()
        if count[0] == 0:
            db.execute('''INSERT INTO USERS (Username , Email , Password)
            VALUES (? , ? , ?);''' , (data[2] , data[3] , data[4]))
            userdb.commit()
            udp.sendto("Register successfully.".encode() , udp_addr)
        else:
            udp.sendto("Username is already used.".encode() , udp_addr)
        userdb.close()
    else:
        udp.sendto("Usage: register <username> <email> <password>".encode() , udp_addr)

def Login(data , conn):
    if len(data) == 4:
        userdb = sqlite3.connect("user.db")
        db = userdb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0] ,))
        client_name = db.fetchone()
        if client_name is  not None:
            message = str(data[0]) + ' ' + "Please logout first."
            conn.sendall(message.encode())
        else:
            db.execute('''SELECT Username FROM USERS WHERE Username = ? AND Password = ?''', (data[2] , data[3] ,))
            fetch = db.fetchone()
            if fetch is  not None:
                client_name = fetch[0]
                random_id = random.randint(1 , 2147483647)
                db.execute('''REPLACE INTO CLIENT (Random_id , Client_name) VALUES (? , ?)''' , (random_id , client_name))
                userdb.commit()
                message = str(random_id) + ' ' + "Welcome, " + client_name + "."
                conn.sendall(message.encode())
            else:
                message = str(data[0]) + " " + "Login failed."
                conn.sendall(message.encode())
        userdb.close()
    else:
        message = str(data[0]) + ' ' + "Usage: login <username> <password>"
        conn.sendall(message.encode())

def Logout(data , conn):
    if len(data) == 2:
        userdb = sqlite3.connect("user.db")
        db = userdb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0] ,))
        client_name = db.fetchone()
        if client_name is  not None:
            db.execute('''DELETE FROM CLIENT WHERE Random_id = ?''', (data[0] , ))
            userdb.commit()
            string = "Bye, " + client_name[0] + "."
            conn.sendall(string.encode())
        else:
            conn.sendall("Please login first.".encode())
        userdb.close()
    else:
        conn.sendall("Usage: logout".encode())

def Whoami(data , udp_addr):
    if len(data) == 2:
        userdb = sqlite3.connect("user.db")
        db = userdb.cursor()
        db.execute('''SELECT Client_name FROM CLIENT WHERE Random_id = ?''', (data[0] ,))
        client_name = db.fetchone()
        userdb.close()
        if client_name is not None:
            udp.sendto(client_name[0].encode() , udp_addr)
        else:
            udp.sendto("Please login first.".encode() , udp_addr)
    else:
        udp.sendto("Usage: whoami".encode() , udp_addr)

def List_user(data , conn):
    if len(data) == 2:
        userdb = sqlite3.connect("user.db")
        db = userdb.cursor()
        db.execute('''SELECT Username , Email FROM USERS''')
        row = db.fetchall()
        userdb.close()
        string = "Name\tEmail"
        for r in row:
            string += '\n' + r[0] + '\t' + r[1]
        conn.sendall(string.encode())
    else:
        conn.sendall("Usage: list-user".encode())

HOST = "127.0.0.1"
PORT = int(sys.argv[1])

tcp = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
tcp.bind((HOST , PORT))
tcp.listen(50)

udp = socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
udp.bind((HOST , PORT))

userdb = sqlite3.connect("user.db" , check_same_thread=False)
db = userdb.cursor()
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
userdb.commit()
userdb.close()

tcp_connect = threading.Thread(target = connect_tcp , args=())
tcp_connect.start()
udp_read = threading.Thread(target = read_udp , args=())
udp_read.start()