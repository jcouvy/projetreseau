from grid import *

"""
The Termios import is used to flush the wild inputs that can interfere with the game.
It works only on UNIX systems.
"""

from termios import tcflush, TCIFLUSH

import sys
import socket
import select

"""
The client socket is created and the connection to the server is made.
In the infinite loop, the protocol messages are received, split if necessary,
then the execute function handles the messages.

"""


def start_client(address):
    nickname = str(input("Indiquez votre nickname : "))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
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
            #command = command.strip("GRID ")
            command = command.replace("GRID ", "")

            for i in range(9):
                grid.cells[i] = int(command[i])

            grid.display()

        if command.startswith("PLAY"):
            tcflush(sys.stdin, TCIFLUSH)
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

        if command.startswith("OCCUPIED"):
            print("La case que vous souhaitiez jouer est occupée. Veuillez en sélectionner une autre.")

        if command.startswith("LISTU"):
            #list = command.strip("LISTU ")
            list = command.replace("LISTU", "")
            usernames = list.split(',')
            print("Liste des utilisateurs : ")
            for name in usernames:
                if name != "":
                    print(name)

        if command.startswith("LISTG"):
            #list = command.strip("LISTG ")
            list = command.replace("LISTG", "")
            game_types = list.split(';')
            if game_types[0] != "":
                print("Liste des parties en cours : ")
                games = game_types[0].split(',')
                for game in games:
                    if game != "":
                        print(game)
            elif game_types[1] != "":
                print("Liste des parties libres : ")
                games = game_types[1].split(',')
                for game in games:
                    if game != "":
                        print(game)


        if command.startswith("MSG"):
            #message = command.strip("MSG")
            message = command.replace("MSG ", "")
            print(message)

        if command.startswith("CMD"):
            cmd = input("$> ")
            socket.send(bytearray(cmd, "utf-8"))

