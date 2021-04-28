#!/usr/bin/python3
import sys
import socket


def gettype(msg):
    tcp_cmd = ["login", "logout", "list-user", "exit"]
    udp_cmd = ["register", "whoami"]
    name = msg.split()
    if ((name[0] in tcp_cmd) == True):
        return "tcp"
    elif ((name[0] in udp_cmd) == True):
        return "udp"
    else:
        return "tcp"


def if_id_returns(msg):
    tmp_list = msg.split("__")
    id = tmp_list[0]
    if (id.isnumeric()):
        id = int(id)
        length = len(tmp_list)
        if (length >= 2):
            msg = tmp_list[1]
        return id, msg
    else:
        return - 1, msg


def custom_print(msg):
    if msg == "" or msg == " ":
        return
    tmp_list = msg.split(" ")
    if tmp_list[0] == "Name":  # returns "list-user"
        i = 0
        for tmp in tmp_list:
            if (i % 2) == 0:
                print("{:<9}".format(tmp), end="")
            elif i % 2:
                print(tmp)
            i += 1
    else:
        print(msg)


if (__name__ == "__main__"):
    # get server info
    if len(sys.argv) != 3 or sys.argv[2].isnumeric() == False:
        print("Usage: {} <server ipv4 address> <port>".format(sys.argv[0]))
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    # print(type(host), " ", type(port))
    server_address = (host, port)

    # client info
    ID = -1
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect(server_address)
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print("Error connecting server")
        sys.exit(1)
    print("********************************\n** Welcome to the BBS server. **\n********************************")
    try:
        while True:
            msg = input("% ")
            if msg != "" and msg != " ":
                type = gettype(msg)
                if (type == "tcp"):
                    data = msg.encode()
                    tcp_sock.sendall(data)
                    data = tcp_sock.recv(1024)
                    msg = data.decode()
                    # print("yuanshi: ", msg)
                    tmp_id, msg = if_id_returns(msg)
                    if (tmp_id != -1):
                        ID = tmp_id
                    if (msg == "*EXIT"):
                        break
                    custom_print(msg)
                elif (type == "udp"):
                    msg = str(ID) + " " + msg
                    data = msg.encode()
                    udp_sock.sendto(msg.encode(), server_address)
                    data, _ = udp_sock.recvfrom(1024)
                    msg = data.decode()
                    print(msg)
    finally:
        tcp_sock.close()
        udp_sock.close()

# tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# tcp_sock.connect(server_address)
# try:
#     msg = input("type message: ")
#     tcp_sock.sendall(msg.encode())
#     while True:
#         data = (tcp_sock.recv(1024)).decode("utf-8")
#         if (data != "" and data != None):
#             print("received {}".format(data))
#         else:
#             break
# finally:
#     print("closing socket")
#     tcp_sock.close()

# udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# try:
#     msg = input("type message: ")
#     print('sending {!r}'.format(msg))
#     sent = udp_sock.sendto(msg.encode(), server_address)
#     print('waiting to receive')
#     data, server = udp_sock.recvfrom(4096)
#     print('received {!r}'.format(data))
# finally:
#     print('closing socket')
#     udp_sock.close()
