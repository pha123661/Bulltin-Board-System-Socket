#!/usr/bin/python3
import socket
from sys import exit
from argparse import ArgumentParser

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
    except:
        print("Error connecting server")
        exit(1)
    print("********************************\n** Welcome to the BBS server. **\n********************************")
    try:
        while True:
            msg = input("% ")
            if msg != "" and msg != " ":
                tcp_sock.sendall(msg.encode())
                msg = tcp_sock.recv(4096).decode()
                if msg == "*EXIT":
                    break
                print(msg)
    finally:
        tcp_sock.close()
