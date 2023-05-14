#!/usr/bin/python3
import socket
import sqlite3
import threading
from argparse import ArgumentParser
from datetime import datetime


# global vars
SN = 1
SN_Lock = threading.Lock()
Posts = []  # list of class post
P_Lock = threading.Lock()
Board = []  # list of tuple(name, mod)
B_Lock = threading.Lock()


class post():
    def __init__(self, owner, board, title, content, time=datetime.today().strftime("%m/%d")):
        with SN_Lock:
            global SN
            self.SN = SN
            SN += 1

        self.owner = owner
        self.board = board
        self.title = title
        self.content = content.replace("<br>", "\n")
        self.time = time
        self.comment = []  # list of tuple(user, comment)
        self.Lock = threading.Lock()

    def update_title(self, title):
        with self.Lock:
            self.title = title

    def update_content(self, content):
        with self.Lock:
            self.content = content.replace("<br>", "\n")

    def add_comment(self, user, comment):
        with self.Lock:
            self.comment.append((user, comment))


class server(threading.Thread):
    def __init__(self, sock):
        super().__init__()
        self.socket = sock
        self.username = ""
        self.useremail = ""
        self.cmd = []

    def run(self):
        print("New connection.")
        # database
        self.connection_sqlite = sqlite3.connect("my_db.db")
        self.cursor_sqlite = self.connection_sqlite.cursor()
        self.cursor_sqlite.execute(
            """CREATE TABLE IF NOT EXISTS USERS(
                UID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT NOT NULL UNIQUE,
                Email TEXT NOT NULL,
                Password TEXT NOT NULL) """)

        while True:
            data = self.socket.recv(4096)
            if data:
                if not self.parse(data.decode()):
                    msg = self.get_usage(self.cmd[0])
                else:
                    msg = self.execute()
                self.socket.sendall(msg.encode())
                if msg == "*EXIT":
                    break
            else:
                break

        self.socket.close()

    def parse(self, msg):
        available = ["login", "logout", "list-user", "exit", "register", "whoami",
                     "create-board", "create-post", "list-board", "list-post",
                     "read", "delete-post", "update-post", "comment"]
        self.cmd = msg.split()
        if self.cmd[0] not in available:
            return False
        if self.cmd[0] == "login" and len(self.cmd[1:]) != 2:
            return False
        if self.cmd[0] == "register" and len(self.cmd[1:]) != 3:
            return False
        if self.cmd[0] == "create-board" and len(self.cmd[1:]) != 1:
            return False
        if self.cmd[0] == "create-post":  # cmd = "create-post", <board>, <title>, <content>
            try:
                tmp_list = ["create-post", ]
                tmp = msg.split("--title")[0]
                tmp = tmp.split()[1]
                tmp_list.append(tmp)
                tmp = msg.split("--title")[1]
                tmp = tmp.split("--content")[0].strip(" ")
                tmp_list.append(tmp)
                tmp = msg.split("--content")[1].strip(" ")
                tmp_list.append(tmp)
                self.cmd = tmp_list
            except IndexError:  # format wrong
                return False
        if self.cmd[0] == "list-post" and len(self.cmd[1:]) != 1:
            return False
        if self.cmd[0] == "read":
            if len(self.cmd[1:]) != 1:
                return False
            else:
                self.cmd[1] = int(self.cmd[1])  # SN
        if self.cmd[0] == "delete-post":
            if len(self.cmd[1:]) != 1:
                return False
            else:
                self.cmd[1] = int(self.cmd[1])  # SN
        if self.cmd[0] == "update-post":  # cmd = update-post, <type>, <SN>, <content>
            try:
                tmp_list = ["update-post"]
                if msg.find("--title") != -1:
                    tmp_list.append("title")
                    tmp = msg.split("--title")[0]
                    tmp = int(tmp.split()[1])
                    tmp_list.append(tmp)
                    tmp = msg.split("--title")[1].strip(" ")
                    tmp_list.append(tmp)
                elif msg.find("--content") != -1:
                    tmp_list.append("content")
                    tmp = msg.split("--content")[0]
                    tmp = int(tmp.split()[1])
                    tmp_list.append(tmp)
                    tmp = msg.split("--content")[1].strip(" ")
                    tmp_list.append(tmp)
                self.cmd = tmp_list
                if len(self.cmd[1:]) != 3:
                    return False
            except IndexError:
                return False
        if self.cmd[0] == "comment":
            if len(self.cmd[1:]) < 2:
                return False
            else:
                self.cmd[1] = int(self.cmd[1])
                tmp_list = ["comment", self.cmd[1]]
                tmp_list.append(msg.split(str(self.cmd[1]))[1].strip(" "))
                self.cmd = tmp_list
        return True

    def get_usage(self, msg):
        if msg == "register":
            return "Usage: register <username> <email> <password>"
        if msg == "login":
            return "Usage: login <username> <password>"
        if msg == "create-board":
            return "Usage: create-board <name>"
        if msg == "create-post":
            return "Usage: create-post <board-name> --title <title> --content <content>"
        if msg == "list-post":
            return "Usage: list-post <board-name>"
        if msg == "read":
            return "Usage: read <post-S/N>"
        if msg == "delete-post":
            return "Usage: delete-post <post-S/N>"
        if msg == "update-post":
            return "Usage: update-post <post-S/N> --title/content <new>"
        if msg == "comment":
            return "Usage: comment <post-S/N> <comment>"
        else:
            return msg + ": command not found."

    def execute(self):
        if self.cmd[0] == "register":
            return self.register(self.cmd[1], self.cmd[2], self.cmd[3])
        if self.cmd[0] == "login":
            return self.login(self.cmd[1], self.cmd[2])
        if self.cmd[0] == "logout":
            return self.logout()
        if self.cmd[0] == "whoami":
            return self.whoami()
        if self.cmd[0] == "list-user":
            return self.list_user()
        if self.cmd[0] == "exit":
            return self.exit()
        if self.cmd[0] == "create-board":
            return self.create_board(self.cmd[1])
        if self.cmd[0] == "create-post":
            return self.create_post(self.cmd[1], self.cmd[2], self.cmd[3])
        if self.cmd[0] == "list-board":
            return self.list_board()
        if self.cmd[0] == "list-post":
            return self.list_post(self.cmd[1])
        if self.cmd[0] == "read":
            return self.read_post(self.cmd[1])
        if self.cmd[0] == "delete-post":
            return self.delete_post(self.cmd[1])
        if self.cmd[0] == "update-post":
            return self.update_post(self.cmd[1], self.cmd[2], self.cmd[3])
        if self.cmd[0] == "comment":
            return self.comment(self.cmd[1], self.cmd[2])

    def register(self, name, email, pwd):
        for user_info in self.cursor_sqlite.execute("SELECT * FROM USERS"):
            if (user_info[1] == name):
                return "Username is already used."
        self.cursor_sqlite.execute(
            "INSERT INTO USERS (Username, Email, Password) VALUES (?, ?, ?)", (name, email, pwd))
        self.connection_sqlite.commit()
        return "Register successfully."

    def login(self, name, pwd):
        if self.username != "":
            return "Please logout first."
        for user_info in self.cursor_sqlite.execute("SELECT * FROM USERS"):
            if user_info[1] == name and user_info[3] == pwd:
                self.username = name
                tmp_cursor = self.cursor_sqlite.execute(
                    "SELECT * FROM USERS WHERE Username = ?", (name,))  # get email
                for tmp_info in tmp_cursor:
                    self.useremail = tmp_info[2]

                return "Welcome, " + name + "."

        return "Login failed."

    def logout(self):
        if self.username == "":
            return "Please login first."
        tmp = self.username
        self.username = ""
        self.useremail = ""
        return "Bye, {}.".format(tmp)

    def whoami(self):
        if self.username == "":
            return "Please login first."
        else:
            return self.username

    def list_user(self):
        msg = "Name        Email"
        for user_info in self.cursor_sqlite.execute("SELECT * FROM USERS"):
            msg = msg + "\n" + user_info[1] + " " * \
                (12 - len(user_info[1])) + user_info[2]
        return msg

    def exit(self):
        return "*EXIT"

    def create_board(self, name):
        if self.username == "":
            return "Please login first."
        with B_Lock:
            for b in Board:
                if b[0] == name:
                    return "Board already exists."
            Board.append((name, self.username))
        return "Create board successfully."

    def create_post(self, board, title, content):
        if self.username == "":
            return "Please login first."
        flag = 0
        with B_Lock:
            for b in Board:
                if b[0] == board:
                    flag = 1
                    break
        if flag == 0:
            return "Board does not exist."
        with P_Lock:
            Posts.append(post(self.username, board, title, content))
        return "Create post successfully."

    def list_board(self):
        msg = "Index       Name                Moderator"
        with B_Lock:
            for i in range(len(Board)):
                msg = msg + "\n" + \
                    str(i+1) + " "*(12 - len(str(i+1))) + \
                    Board[i][0] + " "*(20 - len(Board[i][0])) + \
                    Board[i][1] + " " * (12 - len(Board[i][1]))
        return msg

    def list_post(self, board):
        msg = "S/N         Title               Author      Date"
        flag = 0
        with P_Lock:
            for p in Posts:
                if p.board == board:
                    flag = 1
                    msg = msg + "\n" + str(p.SN) + " " * (12 - len(str(p.SN))) +\
                        p.title + " " * (20 - len(p.title)) +\
                        p.owner + " " * (12 - len(p.owner)) +\
                        str(p.time)
        if flag == 0:
            with B_Lock:
                for b in Board:
                    if b[0] == board:
                        return msg
            return "Board does not exist."
        else:
            return msg

    def read_post(self, sn):
        with P_Lock:
            for p in Posts:
                if p.SN == sn:
                    msg = "Author: " + p.owner + "\n" +\
                        "Title: " + p.title + "\n" +\
                        "Date: " + p.time + "\n" +\
                        "--" + "\n" + \
                        p.content + "\n" + \
                        "--"
                    for c in p.comment:
                        msg = msg + "\n" + c[0] + ": " + c[1]
                    return msg
        return "Post does not exist."

    def delete_post(self, sn):
        if self.username == "":
            return "Please login first."
        with P_Lock:
            for i in range(len(Posts)):
                if Posts[i].SN == sn:
                    if Posts[i].owner == self.username:
                        Posts.pop(i)
                        return "Delete successfully."
                    else:
                        return "Not the post owner."
        return "Post does not exist."

    def update_post(self, type, sn, content):
        if self.username == "":
            return "Please login first."
        with P_Lock:
            for p in Posts:
                if p.SN == sn:
                    if p.owner == self.username:
                        if type == "title":
                            p.update_title(content)
                        elif type == "content":
                            p.update_content(content)
                        return "Update successfully."
                    else:
                        return "Not the post owner."
        return "Post does not exist."

    def comment(self, sn, comment):
        if self.username == "":
            return "Please login first."
        with P_Lock:
            for p in Posts:
                if p.SN == sn:
                    p.add_comment(self.username, comment)
                    return "Comment successfully."
        return "Post does not exist."


if __name__ == "__main__":
    # get server info
    parser = ArgumentParser()
    parser.add_argument("port", type=int)
    host = "0.0.0.0"
    port = parser.parse_args().port
    server_address = (host, port)

    # create socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(server_address)
    tcp_sock.listen(10)

    # accept client
    try:
        while True:
            client_socket, _ = tcp_sock.accept()
            server(client_socket).start()
    finally:
        tcp_sock.close()
