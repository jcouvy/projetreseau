from grid import *
import socket
import select
import time

"""
The client socket is created and the connection to the server is made.
In the infinite loop, the protocol messages are received, split if necessary,
then the execute function handles the messages.

"""


def start_client(address):
    nickname = str(input("Indiquez votre nickname : "))

    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((address, 8888))
    s.setblocking(True)
    grid = Grid()

    if nickname:
        s.send(bytearray("NICK " + nickname, "utf-8"))

    while True:
        s_to_read, _, _ = select.select([s], [], [])
        for tmp_s in s_to_read:
            server_msg = tmp_s.recv(4096)
            print(server_msg)
            str_message = server_msg.decode("utf-8")
            commands = str_message.split('$')
            execute(commands, grid, tmp_s)

"""
This function handles the different messages sent from the server.

"""


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

        if command.startswith("WIN"):
            print("Vous avez gagné! Félicitations!")

        if command.startswith("LOSE"):
            print("Vous avez perdu! Essayez encore!")

        if command.startswith("DRAW"):
            print("Cette partie se conclue avec une égalité parfaite!")

        if command.startswith("INVALID"):
            print("Veuillez entrer un entier valide (entre 0 et 8).")
