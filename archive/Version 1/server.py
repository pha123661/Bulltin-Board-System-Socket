#!/usr/bin/python3
import socket
import sys
import select
import os
import signal
import sqlite3
import random

filename = ".online_users.txt"


class CMD():
    def __init__(self):
        self.command = ""
        self.args = []
        self.ID = -1


class ct_status():
    def __init__(self):
        self.user_name = ""
        self.user_email = ""
        self.ID = -1  # 1 <= ID <= 100000

    def clear(self):
        self.user_name = ""
        self.user_email = ""
        self.ID = -1  # 1 <= ID <= 100000


def parse_tcp(msg, cmd):
    available_commands = ["login", "logout", "list-user", "exit"]
    tmp_list = msg.split()
    cmd.command = tmp_list[0]
    cmd.args = tmp_list[1:]
    # verify
    if ((cmd.command in available_commands) == False):
        return False
    if (cmd.command == "login" and len(cmd.args) != 2):
        return False
    return True


def parse_udp(msg, cmd):
    available_commands = ["register", "whoami"]
    tmp_list = msg.split()
    cmd.ID = tmp_list[0]
    cmd.command = tmp_list[1]
    cmd.args = tmp_list[2:]
    # verify
    if ((cmd.command in available_commands) == False):
        return False
    if (cmd.command == "register" and len(cmd.args) != 3):
        return False
    return True


def get_usage(msg):
    if (msg == "register"):
        return "Usage: register <username> <email> <password>"
    elif (msg == "login"):
        return "Usage: login <username> <password>"
    else:
        return msg + ": command not found."


# user_info(in db) = (uid, "name", "email", "password")
def run_tcp_command(cmd, status=None):
    # login
    if (cmd.command == "login"):
        if (status.user_name != ""):
            return "Please logout first."
        for user_info in cursor_sqlite.execute("SELECT * FROM USERS"):
            # name and password valild
            if (user_info[1] == cmd.args[0] and user_info[3] == cmd.args[1]):
                status.user_name = cmd.args[0]
                tmp_cursor = cursor_sqlite.execute(
                    "SELECT * FROM USERS WHERE Username = ?", (cmd.args[0],))  # get email
                for tmp_info in tmp_cursor:
                    status.user_email = tmp_info[2]
                random.seed(None)
                status.ID = random.randint(1, 100000)
                # print("login as {} {} {}".format(status.ID, status.user_name,
                #                                  status.user_email))
                # update "shared memory"
                with open(filename, "a") as file:
                    tmp = " " + str(status.ID) + " " + status.user_name
                    file.write(tmp)

                return str(status.ID) + "__" + "Welcome, " + cmd.args[0] + "."
        return "Login failed."

    # logout
    if (cmd.command == "logout"):
        if (status.user_name == ""):
            return "Please login first."
        else:
            tmp_list = []
            # update "shared memory"
            with open(filename, "r") as file:
                tmp = file.read()
                tmp_list = tmp.split(" ")
            try:
                # print("tmp list = ", tmp_list)
                idx = tmp_list.index(str(status.ID))
                tmp_list.pop(idx)
                tmp_list.pop(idx)  # yuan ben shi idx + 1
                # print("poped tmp list = ", tmp_list)
            except:
                print("logout: error updating shared memory")
            with open(filename, "w") as file:
                for tmp in tmp_list:
                    if (tmp != " " and tmp != ""):
                        file.write(tmp + " ")

            tmp = status.user_name
            status.clear()
            return "Bye, {}.".format(tmp)

    # list-user
    if (cmd.command == "list-user"):
        rt_msg = "Name Email"
        for user_info in cursor_sqlite.execute("SELECT * FROM USERS"):
            rt_msg = rt_msg + " " + user_info[1] + " " + user_info[2]
        return rt_msg

    # exit
    if (cmd.command == "exit"):
        return "*EXIT"


def run_udp_command(cmd):
    # register
    if (cmd.command == "register"):
        for user_info in cursor_sqlite.execute("SELECT * FROM USERS"):
            if (user_info[1] == cmd.args[0]):
                return "Username is already used."
        cursor_sqlite.execute(
            "INSERT INTO USERS (Username, Email, Password) VALUES (?, ?, ?)", (cmd.args[0], cmd.args[1], cmd.args[2]))
        connection_sqlite.commit()
        return "Register successfully."
    # whoami
    if (cmd.command == "whoami"):
        # read "shared memory"
        with open(filename, "r") as file:
            tmp = file.read()
            tmp_list = tmp.split(" ")
            # print("tmp_list = ", tmp_list)
            try:
                idx = tmp_list.index(cmd.ID)
                return str(tmp_list[idx+1])
            except:
                return "Please login first."


def dosomething_tcp(sock, data, status):  # data = byte type
    # sock.sendall(data)
    cmd = CMD()
    msg = data.decode()  # string type
    if (parse_tcp(msg, cmd) == False):  # command error
        rt_msg = get_usage(cmd.command)
    else:
        rt_msg = run_tcp_command(cmd, status)
    data = rt_msg.encode()
    sock.sendall(data)
    if (rt_msg == "*EXIT"):
        return "*EXIT"
    return "O"  # this is ou not zero


def dosomething_udp(sock, data, client_address):
    # sock.sendto(data, client_address)
    cmd = CMD()
    msg = data.decode()
    if (parse_udp(msg, cmd) == False):
        rt_msg = get_usage(cmd.command)
    else:
        rt_msg = run_udp_command(cmd)
    data = rt_msg.encode()
    sock.sendto(data, client_address)

    # database
connection_sqlite = sqlite3.connect("my_db.db")
cursor_sqlite = connection_sqlite.cursor()
cursor_sqlite.execute(
    """CREATE TABLE IF NOT EXISTS USERS(
        UID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT NOT NULL UNIQUE,
        Email TEXT NOT NULL,
        Password TEXT NOT NULL)""")


if (__name__ == "__main__"):
    # get server info
    if len(sys.argv) != 2 or sys.argv[1].isnumeric == False:
        print("Usage: {} <port>".format(sys.argv[0]))
        sys.exit(1)
    host = "0.0.0.0"
    port = int(sys.argv[1])
    server_address = (host, port)
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    # create tcp socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # set socket can be reused immediately after closed
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(server_address)
    tcp_sock.setblocking(0)  # async listen
    tcp_sock.listen(5)

    # create udp socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set socket can be reused immediately after closed
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind(server_address)

    # set up select
    input = []
    input.append(tcp_sock)
    input.append(udp_sock)

    # init file based "shared memory"
    with open(filename, "w") as file:
        file.write(" -2 NULL")

    # get msg
    try:
        while True:
            # ignore timeout value == block until input
            readable = select.select(input, [], [])[0]
            for sock in readable:
                if (sock is tcp_sock):  # tcp connection -> accept
                    tcp_connection, _ = sock.accept()
                    print("New connection.")
                    if(os.fork() == 0):
                        status = ct_status()
                        while True:
                            data = tcp_connection.recv(1024)  # block here
                            # print("data =", data)
                            flag = ""
                            if (data):
                                flag = dosomething_tcp(
                                    tcp_connection, data, status)
                            if (not data):
                                break
                            if (flag == "*EXIT"):
                                break
                        # print("Closing connection.")
                        tcp_connection.close()
                        os._exit(0)
                elif (sock is udp_sock):  # udp recv -> recv and do
                    data, client_address = sock.recvfrom(1024)
                    if (data):
                        dosomething_udp(sock, data, client_address)
    # shutdown
    finally:
        # print("\nShutting down server...")
        for sock in input:
            sock.close()
        if (os.path.exists(filename)):
            os.remove(filename)
