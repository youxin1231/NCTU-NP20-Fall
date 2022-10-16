import sys
import time
import select
import socket
import threading
from datetime import datetime


def Create_chatroom(host, port, owner):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.settimeout(0.1)
    server.bind((host, port))
    time.sleep(0.1)
    server.listen(10)
    while True:
        if kill_thread:
            server.close()
            return
        try:
            conn, addr = server.accept()
            list_of_clients.append(conn)
            thread_client = threading.Thread(
                target=clientthread, args=(conn, addr, owner,))
            thread_client.start()
        except socket.timeout:
            pass


def clientthread(conn, addr, owner):
    client_name = str(conn.recv(1024), encoding='utf-8')
    conn.sendall(
        "***************************\n**Welcome to the chatroom**\n***************************".encode())
    time.sleep(0.05)
    conn.sendall(owner.encode())
    time.sleep(0.05)
    mes_to_send = ''
    for mes in message_history[-3:]:
        if mes != message_history[-1]:
            mes += "\n"
        mes_to_send += mes
    conn.sendall(mes_to_send.encode())
    now = datetime.now()
    now_time = now.strftime("%H:%M")
    message_to_send = "sys [" + now_time + "] : " + \
        client_name + " join us."
    if not attach:
        broadcast(message_to_send, conn)
    while True:
        message = str(conn.recv(1024), encoding='utf-8')
        if message:
            now = datetime.now()
            now_time = now.strftime("%H:%M")
            if message[-20:] == "Welcome back to BBS.":
                conn.close()
                remove(conn)
                return
            elif message == "Close chatroom.":
                string = "sys[" + now_time + "] : the chatroom is close.\nWelcome back to BBS."
                broadcast(string, conn)
                conn.close()
                remove(conn)
                return
            elif message[0:5] == "sys [":
                broadcast(message, conn)
                conn.close()
                remove(conn)
                return
            elif message == "detach":
                conn.close()
                remove(conn)
                return
            else:
                message_to_send = client_name + \
                    "[" + now_time + "] : " + message
                message_history.append(message_to_send)
                broadcast(message_to_send, conn)
        else:
            remove(conn)


def broadcast(message, connection):
    for clients in list_of_clients:
        if clients != connection:
            clients.sendall(message.encode())


def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)


def Join_chatroom(host, port, client_name):
    global kill_thread
    client_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_server.connect((host, port))
    client_server.sendall(client_name.encode())
    WelcomeMessage = str(client_server.recv(1024), encoding='utf-8')
    print(WelcomeMessage)
    owner = str(client_server.recv(1024), encoding='utf-8')
    while True:
        sockets_list = [sys.stdin, client_server]
        read_sockets, write_socket, error_socket = select.select(
            sockets_list, [], [])
        for socks in read_sockets:
            if socks == client_server:
                message = str(client_server.recv(1024), encoding='utf-8')
                print(message)
                if message[-20:] == "Welcome back to BBS.":
                    client_server.sendall(message.encode())
                    client_server.close()
                    return
            else:
                message = sys.stdin.readline()
                message = message.replace('\n', '')
                if message == "detach" and client_name == owner:
                    client_server.sendall("detach".encode())
                    client_server.close()
                    print("Welcome back to BBS.")
                    return
                elif message == "leave-chatroom" and client_name != owner:
                    now = datetime.now()
                    now_time = now.strftime("%H:%M")
                    message_to_send = "sys [" + now_time + "] : " + \
                        client_name + " leave us."
                    client_server.sendall(message_to_send.encode())
                    client_server.close()
                    print("Welcome back to BBS.")
                    return
                elif message == "leave-chatroom" and client_name == owner:
                    string = "close-chatroom " + owner
                    tcp.sendall(string.encode())
                    client_server.sendall("Close chatroom.".encode())
                    client_server.close()
                    kill_thread = True
                    print("Welcome back to BBS.")
                    return
                else:
                    client_server.sendall(message.encode())


HOST = sys.argv[1]
PORT = int(sys.argv[2])

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect((HOST, PORT))
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
WelcomeMessage = str(tcp.recv(1024), encoding='utf-8')
print(WelcomeMessage)
client_id = 0
attach = False
kill_thread = False
list_of_clients = []
message_history = []

while True:
    string = str(client_id) + ' ' + input('% ')
    data = string.split()
    if data[1] == 'register' or data[1] == 'whoami' or data[1] == 'list-chatroom':
        udp.sendto(string.encode(), (HOST, PORT))
        ServerMessage, addr = udp.recvfrom(1024)
        print(ServerMessage.decode('utf-8'))
    elif data[1] == 'login':
        tcp.sendall(string.encode())
        ServerMessage = str(tcp.recv(1024), encoding='utf-8')
        ServerMessage = ServerMessage.split(' ', 1)
        client_id = ServerMessage[0]
        ServerMessage = ServerMessage[1]
        print(ServerMessage)
    elif data[1] == 'logout' or data[1] == 'list-user' or data[1] == 'create-board' or data[1] == 'create-post' or data[1] == 'list-board' or data[1] == 'list-post' or data[1] == 'read' or data[1] == 'delete-post' or data[1] == 'update-post' or data[1] == 'comment' or data[1] == 'create-chatroom' or data[1] == 'join-chatroom' or data[1] == 'attach' or data[1] == 'restart-chatroom':
        tcp.sendall(string.encode())
        ServerMessage = str(tcp.recv(1024), encoding='utf-8')
        if ServerMessage[0:25] == "start to create chatroom…":
            message = ServerMessage.split()
            ServerMessage = message[0] + " " + \
                message[1]+" " + message[2] + " " + message[3]
            print(ServerMessage)
            chatroom_thread = threading.Thread(
                target=Create_chatroom, args=(HOST, int(data[2]), message[4],))
            chatroom_thread.start()
            Join_chatroom(HOST, int(data[2]), message[4])
        elif ServerMessage[0:15] == "Attach success.":
            attach = True
            message = ServerMessage.split()
            Join_chatroom(HOST, int(message[2]), message[3])
        elif ServerMessage[0:13] == "Join success.":
            attach = False
            message = ServerMessage.split()
            Join_chatroom(HOST, int(message[2]), message[3])
        elif ServerMessage[0:16] == "Restart success.":
            kill_thread = False
            message = ServerMessage.split()
            chatroom_thread = threading.Thread(
                target=Create_chatroom, args=(HOST, int(message[2]), message[3],))
            chatroom_thread.start()
            print("start to create chatroom…")
            Join_chatroom(HOST,int(message[2]), message[3])
        else:
            print(ServerMessage)
    elif data[1] == 'exit':
        tcp.sendall(string.encode())
        tcp.close()
        udp.close()
        break
    else:
        print("Command not fonund.")
