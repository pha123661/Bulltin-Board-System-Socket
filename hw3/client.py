#!/usr/bin/python3
import socket
import threading
import sys
import pickle
from time import sleep
from datetime import datetime
from select import select
from argparse import ArgumentParser

mode = "BBS"   # "BBS" or "CHATROOM"
username = ""  # username

History = []   # last three chat history


def get_name(tcp_sock):
    tcp_sock.sendall(b"whoami")
    msg = tcp_sock.recv(4096).decode()
    if msg == "Please login first.":
        return ""
    else:
        return msg


class Chatroom_server(threading.Thread):
    def __init__(self, BBS, port):
        super().__init__()
        # create socket
        self.server_address = ("0.0.0.0", int(port))
        self.master_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.master_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.master_sock.bind(self.server_address)
        self.master_sock.listen(10)
        self.master_sock.setblocking(0)  # async
        self.input_sock = [self.master_sock, ]
        self.BBS_sock = BBS

    def run(self):
        Terminated = False
        while not Terminated:
            readable, _, _ = select(self.input_sock, [], [])
            for sock in readable:
                if sock is self.master_sock:
                    client_socket, _ = sock.accept()
                    self.input_sock.append(client_socket)
                    name = client_socket.recv(4096).decode()
                    if name != username:
                        msg = "sys " + \
                            datetime.today().strftime(
                                "[%H:%M]") + ": " + name + " join us."
                        self.Broadcast_except(client_socket, msg)
                    for h in History:
                        sleep(1/10000)
                        client_socket.sendall(h.encode())

                else:
                    data = sock.recv(4096)
                    data = pickle.loads(data)
                    msg = data["name"] + " " + \
                        data["time"] + ": " + data["msg"]

                    if data["msg"] == "leave-chatroom":
                        if data["name"] == username:  # close server
                            msg = "sys " + \
                                datetime.today().strftime(
                                    "[%H:%M]") + ": the chatroom is close."
                            self.Broadcast_except(sock, msg)
                            sleep(1 / 10000)  # important
                            self.Broadcast_except(None, "*CLOSE")
                            for s in self.input_sock:
                                s.close()
                            Terminated = True
                        else:
                            msg = "sys " + \
                                datetime.today().strftime(
                                    "[%H:%M]") + ": " + data["name"] + " leave us."
                            self.Broadcast_except(sock, msg)
                            sock.sendall(b"*CLOSE")
                            sock.close()
                            self.input_sock.remove(sock)
                    elif data["msg"] == "detach" and data["name"] == username:
                        sock.sendall(b"*CLOSE")
                        sock.close()
                        self.input_sock.remove(sock)
                    else:
                        self.update_history(msg)
                        self.Broadcast_except(sock, msg)

        for s in self.input_sock:
            s.close()

        # notify BBS server to update status
        self.BBS_sock.sendall(b"*LEAVE-CHATROOM")
        self.BBS_sock.recv(4096)  # get ACK

    def update_history(self, msg):
        if len(History) >= 3:
            History.pop(0)
        History.append(msg)

    def Broadcast_except(self, except_sock, msg):
        for s in self.input_sock[1:]:
            if s is not except_sock:
                s.sendall(msg.encode())


if __name__ == "__main__":
    # get server info
    parser = ArgumentParser()
    parser.add_argument("ipv4_address", type=str)
    parser.add_argument("port", type=int)
    host = parser.parse_args().ipv4_address
    port = parser.parse_args().port
    server_address = (host, port)
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
            if mode == "BBS":
                msg = input("% ")
                if msg == "list-chatroom":  # send this command using UDP
                    # login or not:
                    if get_name(tcp_sock) == "":
                        print("Please login first.")
                    else:
                        udp_sock.sendto(b"list-chatroom", server_address)
                        data, _ = udp_sock.recvfrom(4096)
                        print(data.decode())
                elif msg != "":
                    tcp_sock.sendall(msg.encode())
                    msg = tcp_sock.recv(4096).decode()

                    # handler
                    if msg == "*EXIT":
                        break
                    elif msg.find("*START") != -1:
                        print("start to create chatroom...")
                        port = int(msg.split("*START")[1])
                        Chatroom_server(tcp_sock, port).start()

                        chatroom_sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        chatroom_sock.connect(("127.0.0.1", port))
                        chatroom_sock.sendall(username.encode())

                        mode = "CHATROOM"
                        print(
                            "*************************\n**​ Welcome to the chatroom​ **\n*************************")
                    elif msg.find("*JOIN") != -1:
                        address = (msg.split("*JOIN")
                                   [0], int(msg.split("*JOIN")[1]))

                        chatroom_sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        chatroom_sock.connect(address)
                        chatroom_sock.sendall(username.encode())

                        mode = "CHATROOM"
                        print(
                            "*************************\n**​ Welcome to the chatroom​ **\n*************************")
                    else:
                        print(msg)
                    # update username after each command
                    username = get_name(tcp_sock)

            elif mode == "CHATROOM":
                input_sock = [sys.stdin, chatroom_sock]
                readable, _, _ = select(input_sock, [], [])
                for sock in readable:
                    if sock is chatroom_sock:
                        msg = chatroom_sock.recv(4096).decode()
                        if msg == "":
                            continue
                        # handler
                        if msg == "*CLOSE":
                            chatroom_sock.close()
                            mode = "BBS"
                            print("Welcome back to BBS.")
                        else:
                            print(msg)
                    elif sock is sys.stdin:
                        msg = sys.stdin.readline()
                        name = username
                        time = datetime.today().strftime("[%H:%M]")
                        msg = msg[0:-1]
                        data = {"name": name, "time": time, "msg": msg}
                        data = pickle.dumps(data)

                        chatroom_sock.sendall(data)

    finally:
        tcp_sock.close()
        udp_sock.close()
