from grid import *
import socket
import select
import time


def start_client(address):
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((address, 8888))
    s.setblocking(True)
    grid = Grid()

    while True:
        s_to_read, _, _ = select.select([s], [], [])
        for tmp_s in s_to_read:
            server_msg = tmp_s.recv(4096)
            print(server_msg)
            str_message = server_msg.decode("utf-8")
            commands = str_message.split('$')
            execute(commands, grid, tmp_s)


def execute(commands, grid, socket):

    for command in commands:
        if command.startswith("GRID "):
            command = command.strip("GRID ")

            for i in range(9):
                grid.cells[i] = int(command[i])

            grid.display()

        if command.startswith("PLAY"):
            shot = input("Quel coup voulez-vous jouer?")
            socket.send(bytearray(shot, "utf-8"))

        if command.startswith("WAIT"):
            print("Votre adversaire est en train de jouer, veuillez patienter...")
