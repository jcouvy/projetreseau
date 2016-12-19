# -*- coding: utf-8 -*-
#!/usr/bin/python3

import socket, select
import re
import sys
import random

from grid import *

"""
Each user (new socket) is defined by 3 arguments:
    - a Socket,
    - an ID, the computer's hostname,
    - the client IP address (v4/v6).
"""
class User:
    def __init__(self, socket, name, ip):
        socket.setblocking(False) # Keeps control in case of error/timeout
        self.socket = socket
        self.name   = name
        self.ip     = ip

    # Necessary with select based TCP server
    def fileno(self):
        return self.socket.fileno()
"""
The class Game gives a few functions to help the server operate the room.
Each game contains:
    - Two players
    # TODO : player array and obs array
    - Three grids (P1, P2, Obs)
    - The next turn
Each byte-message sent by the server to the clients is delimited with a $ sign.
"""
class Game:
    def __init__(self):
        self.playerOne = None
        self.playerTwo = None
        self.gridOne = Grid()
        self.gridTwo = Grid()
        self.gridObs = Grid()
        self.turn = -1

    """
    Fills the Game structure and sends a byte message encoding each player's grid.
    The first turn is chosen with a pseudo random coin-flip.
    """
    def start(self, playerA, playerB):
        self.playerOne = playerA
        self.playerTwo = playerB
        self.turn = random.randint(1,2)

        self.playerOne.socket.send(b'GRID 000000000$')
        self.playerTwo.socket.send(b'GRID 000000000$')

    """
    Send the next turn in a byte-string to each player.
    """
    def send_turn(self):
        assert(self.turn == J1 or self.turn == J2)
        if self.turn == J1:
            self.playerOne.socket.send(b'PLAY$')
            self.playerTwo.socket.send(b'WAIT$')
        else:
            self.playerOne.socket.send(b'WAIT$')
            self.playerTwo.socket.send(b'PLAY$')

    """
    Returns an encoded byte-string of the player's Grid given in arg.
    """
    def encode_grid(self, player):
        msg = "GRID "
        if player == J1:
            for cell in self.gridOne.cells:
                msg = msg + str(cell)
        if player == J2:
            for cell in self.gridTwo.cells:
                msg = msg + str(cell)
        msg = msg + '$'
        return msg.encode('utf-8')

    """
    Decodes the player's move, modifies the according Grid, sends the encoded grid
    back and then updates the turn. Exceptions are raised in order to prevent the server
    from stopping if any player tries an invalid move (i.e: Grid.play() assert fails).
    The player is asked to play again if any exception is caught.
    """
    def handler(self, player, data):
        try:
            cellNum = int(data.decode())
        except ValueError:
            player.socket.send(b'INVALID$')
            player.socket.send(b'PLAY$')
            return

        if self.turn == J1 and player is self.playerOne:
            try:
                print(self.gridOne.cells)
                self.gridObs.play(J1, cellNum)
                self.gridOne.play(J1, cellNum)
                print(self.gridOne.cells)
                
            except AssertionError:
                if (cellNum < 0 or cellNum > NB_CELLS):
                    player.socket.send(b'INVALID$')

                elif (self.gridObs.cells[cellNum] == J2):
                    self.gridOne.cells[cellNum] = J2
                    player.socket.send(self.encode_grid(J1))
                    player.socket.send(b'OCCUPIED$')

                player.socket.send(b'PLAY$')
                return

            player.socket.send(self.encode_grid(J1))
            self.turn = J2

        elif self.turn == J2 and player is self.playerTwo:
            try:
                print(self.gridTwo.cells)
                self.gridObs.play(J2, cellNum)
                self.gridTwo.play(J2, cellNum)
                print(self.gridTwo.cells)

            except AssertionError:
                if (cellNum < 0 or cellNum > NB_CELLS):
                    player.socket.send(b'INVALID$')

                elif (self.gridObs.cells[cellNum] == J1):
                    self.gridTwo.cells[cellNum] = J1
                    player.socket.send(self.encode_grid(J2))
                    player.socket.send(b'OCCUPIED$')

                player.socket.send(b'PLAY$')
                return

            player.socket.send(self.encode_grid(J2))
            self.turn = J1

        if self.game_over() == -1:
            self.send_turn()
        print ('Sending encoded grid to {}'.format(player.name))

    """
    Checks if the game is over (if a win condition is found on the global Grid).
    Send a byte-string to each players according to the output of the game.
    """
    def game_over(self):
        state = self.gridObs.gameOver()
        if state == EMPTY:
            self.playerOne.socket.send(b'DRAW$')
            self.playerTwo.socket.send(b'DRAW$')
        if state == J1:
            self.playerOne.socket.send(b'WIN$')
            self.playerTwo.socket.send(b'LOSE$')
        if state == J2:
            self.playerTwo.socket.send(b'WIN$')
            self.playerOne.socket.send(b'LOSE$')
        return state


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

    print('Server {} started on port {}'.format(socket.gethostbyname(socket.gethostname()),
                                                PORT))

    game = Game()

    while True:
        read_sockets, _ , _ = select.select(connection_list, [], [])

        for client in read_sockets:
            if client is server_socket:
                new_socket, addr = server_socket.accept()
                user = User(new_socket,
                            'Guest'+str(random.randint(0,9999)),
                            addr)
                connection_list.append(user)
                print ('New connection from {} {} '.format(user.name,
                                                           user.ip))

                if (len(connection_list) - 1) == 2:
                    game.start(connection_list[1], connection_list[2])
                    game.send_turn()
                    print ('New game started \n' \
                           ' Player 1: {}\n'     \
                           ' Player 2: {}'.format(game.playerOne.name,
                                                  game.playerTwo.name))

            else:
                data = client.socket.recv(RECV_BUFFER)
                if data:
                    message = data.decode('utf-8')
                    if message.startswith('NICK'):
                        message = message.strip('NICK ')
                        client.name = message
                        break

                    if client == game.playerOne or client == game.playerTwo:
                        print('Received data from {}'.format(client.name))
                        game.handler(client, data)
                    else:
                        print ('Received data from client')
                else:
                    print ('Client {} ({}) disconnected'.format(client.name,
                                                                client.ip))
                    connection_list.remove(client)
                    client.socket.close()

if __name__ == '__main__':
    sys.exit(start_server())
