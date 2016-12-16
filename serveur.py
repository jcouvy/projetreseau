#!/usr/bin/python3

import socket, select
import re
import sys
import random

from grid import *

class User:
    def __init__(self, socket, name, ip):
        socket.setblocking(0) # Keeps control in case of error/timeout
        self.socket = socket
        self.name   = name
        self.ip     = ip

    # Necessary with select based TCP server
    def fileno(self):
        return self.socket.fileno()

class Game:
    def __init__(self):
        playerOne = None
        playerTwo = None
        gridOne = Grid()
        gridTwo = Grid()
        gridObs = Grid()
        turn = -1

    def start(self, playerA, playerB):
        self.playerOne = playerA
        self.playerTwo = playerB
        self.turn = random.randint(1,2)

        self.playerOne.socket.send(b'GRID 000000000\n')
        self.playerTwo.socket.send(b'GRID 000000000\n')

    def send_turn(self):
        assert(self.turn == J1 or self.turn == J2)
        if self.turn == J1:
            self.playerOne.socket.send(b'PLAY\n')
            self.playerTwo.socket.send(b'WAIT\n')
        else:
            self.playerOne.socket.send(b'WAIT\n')
            self.playerTwo.socket.send(b'PLAY\n')

    def encode_grid(self, turn):
        msg = "GRID "
        if turn == J1:
            for cell in self.gridOne:
                msg = msg + str(cell)
        if turn == J2:
            for cell in self.gridTwo:
                msg = msg + str(cell)
        return msg.encode('utf-8')

    def handler(self, player, data):
        cellNum = data.decode()
        if self.turn == J1 and player is self.playerOne:
            self.gridOne.play(J1, cellNum)
            self.gridObs.play(J1, cellNum)
            player.send(encode_grid(self.turn))
            self.turn = J2
        elif self.turn == J2 and player is self.playerTwo:
            self.gridTwo.play(J2, cellNum)
            self.gridObs.play(J2, cellNum)
            player.send(encode_grid(self.turn))
            self.turn = J1

    def game_over(self):
        with self.gridObs.gameOver() as state:
            if state == EMPTY:
                self.playerOne.send(b'GG draw')
                self.playerTwo.send(b'GG draw')
            if state == J1:
                self.playerOne.send(b'GG win')
                self.playerTwo.send(b'GG lose')
            if state == J2:
                self.playerTwo.send(b'GG win')
                self.playerOne.send(b'GG lose')


def start_server():

    HOST = ''
    PORT = 8888
    RECV_BUFFER = 4096

    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    connection_list = []
    connection_list.append(server_socket)

    print('Server started on port {0}'.format(PORT))

    while True:
        read_sockets, _ , _ = select.select(connection_list, [], [])

        for client in read_sockets:
            if client is server_socket:
                new_socket, addr = server_socket.accept()
                user = User(new_socket,
                            socket.gethostname(),
                            socket.gethostbyname(socket.gethostname()))
                connection_list.append(user)
                print ('Client {} ({}) connected'.format(user.name,
                                                         user.ip))

                if (len(connection_list) - 1) % 2 == 0:
                    game = Game()
                    game.start(connection_list[1], connection_list[2])
                    game.send_turn()
                    print ('New game started \n' \
                           ' Player 1: {}\n'     \
                           ' Player 2: {}'.format(game.playerOne.name,
                                                  game.playerTwo.name))

            else:
                data = client.socket.recv(RECV_BUFFER)
                if data:
                    print ('Received data from client')
                    try:
                        game.handler(client, data)
                    except:
                        continue

                else:
                    print ('Client {} ({}) disconnected'.format(client.name,
                                                                client.ip))
                    connection_list.remove(client)
                    client.socket.close()


if __name__ == '__main__':
    sys.exit(start_server())
