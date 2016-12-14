from grid import *
import socket
import select


def start_client(address):

    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((address, 8888))
    grid = Grid()
    grid.display()
    #...TODO...

    while True:
        s_to_read, _, _ = select.select([s], [], [])
        for tmp_s in s_to_read:
            server_msg = tmp_s.recv(32)
            decode(server_msg)


def decode(message):

    msg_str = str(message, "utf-8", "strict")
    if msg_str == "TRY AGAIN"
        #...TODO


