import sys
import socket

HOST = sys.argv[1]
PORT = int(sys.argv[2])

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect((HOST, PORT))
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
WelcomeMessage = str(tcp.recv(1024), encoding='utf-8')
print(WelcomeMessage)
client_id = 0

while True:
    string = str(client_id) + ' ' + input('% ')
    data = string.split()
    if data[1] == 'register' or data[1] == 'whoami':
        udp.sendto(string.encode(), (HOST, PORT))
        ServerMessage , addr = udp.recvfrom(1024)
        print(ServerMessage.decode('utf-8'))
    elif data[1] == 'login':
        tcp.sendall(string.encode())
        ServerMessage = str(tcp.recv(1024), encoding='utf-8')
        ServerMessage = ServerMessage.split(' ' , 1)
        client_id = ServerMessage[0]
        ServerMessage = ServerMessage[1]
        print(ServerMessage)
    elif data[1] == 'logout' or data[1] == 'list-user' or data[1] == 'create-board' or data[1] == 'create-post' or data[1] == 'list-board' or data[1] == 'list-post' or data[1] == 'read' or data[1] == 'delete-post' or data[1] == 'update-post' or data[1] == 'comment':
        tcp.sendall(string.encode())
        ServerMessage = str(tcp.recv(1024), encoding='utf-8')
        print(ServerMessage)
    elif data[1] == 'exit':
        tcp.sendall(string.encode())
        tcp.close()
        udp.close()
        break
    else:
        print("Command not fonund.")