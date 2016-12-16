from grid import *
import socket
import select


def start_client(address):

    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((address, 8888))
    grid = Grid()

    while True:
        s_to_read, _, _ = select.select([s], [], [])
        for tmp_s in s_to_read:
            server_msg = tmp_s.recv(32)
            decode(tmp_s, server_msg, grid)


def decode(socket, message, grid):

    msg_str = message.decode("utf-8")
    if msg_str.startswith("GRID "):
        msg_str = msg_str.strip("GRID ")

        for i in range(9):
            grid.cells[i] = (msg_str[i])

        grid.display()

    if msg_str.startswith("PLAY"):
        shot = int(input("Quel coup voulez-vous jouer?"))
        socket.send(bytearray(shot, "utf-8"))

    if msg_str.startswith("WAIT"):
        print("Votre adversaire est en train de jouer, veuillez patienter...")
