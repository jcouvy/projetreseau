# -*- coding: utf-8 -*-
#!/usr/bin/python3

import socket, select
import re
import sys
import random

from grid import *

P1  = 0
P2  = 1
OBS = 2

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
    - Three grids (P1, P2, Obs)
    - The next turn
Each byte-message sent by the server to the clients is delimited with a $ sign.
"""
class Game:
    def __init__(self, gameId):
        self.id = gameId
        self.players = [None, None]
        self.observators = []
        self.grids = [Grid(), Grid(), Grid()]
        self.turn = -1

    """
    Fills the Game structure and sends a byte message encoding each player's grid.
    The first turn is chosen with a pseudo random coin-flip.
    """
    def start(self, playerA, playerB):
        self.players = [playerA, playerB]
        self.turn = random.randint(1,2)

        self.players[P1].socket.send(b'GRID 000000000$')
        self.players[P2].socket.send(b'GRID 000000000$')

    """
    Send the next turn in a byte-string to each player.
    """
    def send_turn(self):
        assert(self.turn == J1 or self.turn == J2)
        if self.turn == J1:
            self.players[P1].socket.send(b'PLAY$')
            self.players[P2].socket.send(b'WAIT$')
        else:
            self.players[P1].socket.send(b'WAIT$')
            self.players[P2].socket.send(b'PLAY$')

    """
    Returns an encoded byte-string of the player's Grid given in arg.
    """
    def encode_grid(self, player):
        msg = "GRID "
        if player == J1:
            for cell in self.grids[P1].cells:
                msg = msg + str(cell)
        elif player == J2:
            for cell in self.grids[P2].cells:
                msg = msg + str(cell)
        else:
            for cell in self.grids[OBS].cells:
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

        # Each turn is either J1 = 1 or J2 = 2 while P1 is in players[0] and
        # P2 in players[1].
        for i in range (2):
            if self.turn == (i+1) and player is self.players[i]:
                enemy = J2 if (i == P1) else J1
                try:
                    self.grids[OBS].play(i+1, cellNum)
                    self.grids[i].play(i+1, cellNum)

                except AssertionError:
                    if (cellNum < 0 or cellNum >= NB_CELLS):
                        player.socket.send(b'INVALID$')

                    elif (self.grids[OBS].cells[cellNum] == enemy):
                        self.grids[i].cells[cellNum] = enemy
                        player.socket.send(self.encode_grid(i+1))
                        player.socket.send(b'OCCUPIED$')

                    player.socket.send(b'PLAY$')
                    return

                player.socket.send(self.encode_grid(i+1))
                for obs in self.observators:
                    observator.socket.send(self.encode_grid(0))

                self.turn = enemy

                if self.game_over() == -1:
                    self.send_turn()
                print ('Sending encoded grid to {}'.format(player.name))

    """
    Checks if the game is over (if a win condition is found on the global Grid).
    Send a byte-string to each players according to the output of the game.
    """
    def game_over(self):
        state = self.grids[OBS].gameOver()
        if state == EMPTY:
            self.players[P1].socket.send(b'DRAW$')
            self.players[P2].socket.send(b'DRAW$')
        if state == J1:
            self.players[P1].socket.send(b'WIN$')
            self.players[P2].socket.send(b'LOSE$')
        if state == J2:
            self.players[P1].socket.send(b'LOSE$')
            self.players[P2].socket.send(b'WIN$')
        return state


"""
The server contains only 1 Room where 3 games are hosted (by default).
Each user is assigned to the room upon connection. They have access to a set
of commands to :
    - join an active game as observator
    - get some info (list of users/active games)
    - change nickname
    - challenge an other user
Each command is managed server-side by a handling function.
"""
class Room:
    def __init__(self):
        self.games = [Game('northrend'), Game('lordaeron'), Game('kalimdor')]
        self.users = [None]

    """
    Send information parsed in param to every users
    """
    def broadcast_all(self, data):
        msg = 'MSG ' + data + '$'
        for user in self.users:
            user.socket.send(msg.encode('utf-8'))

    """
    Informs the Room when a game starts
    """
    def game_started(self, gameId):
        for game in self.games:
            if game.gameId is gameId:
                print ('New game started in {}\n' \
                       ' Player 1: {}\n'     \
                       ' Player 2: {}'.format(gameId,
                                              game.players[0].name,
                                              game.players[1].name))
        broadcast_all('Une partie demarre à la table '+ gameId +' utilisez join <' + gameId +'> pour observer')

    """
    Appends the user to the observator list of the game named gameId
    """
    def join_game(self, user, gameId):
        for game in self.games:
            if game.gameId is gameId:
                game.observators.append(user)
                # Sending the observator grid upon connection
                user.socket.send(game.encode_grid(0))
        # Removing the user from the Room
        self.users.remove(user)

    # def challenge_user(self, userA, userB):
    #     return

    """
    Send the set of available commands to every users in the Room
    """
    def instructions(self, user):
        msg = "- challenge <username> (défier un joueur)\n \
        - join <game id>  (observer une partie en cours)\n \
        - list games (lister les games)\n \
        - list users\n \
        - nickname <name> (choisir un pseudo)"
        user.socket.send(bytearray("MSG " + msg + "$", "utf-8"))
        user.socket.send('CMD$'.encode('utf-8'))

    """
    Changes the user's name with newName and informs the other users
    """
    def change_username(self, user, newName):
        oldName = user.name
        for u in self.users:
            if u.name == user.name:
                u.name = newName
        print ('Client {} renamed {}'.format(oldName, newName))
        broadcast_all(oldName+' a été renommé en '+newName)
        user.socket.send('CMD$'.encode('utf-8'))

    """
    Send to the user the list of ongoing/empty games
    """
    def list_games(self, user):
        msg = 'LISTG '
        for game in self.games:
            if game.players[P1] != None and game.players[P2] != None:
                msg = msg + game.id + ','
        msg = msg + ";"
        for game in self.games:
            if game.players[P1] == None and game.players[P2] == None:
                msg = msg + game.id + ','
        msg = msg + '$'
        print ('Sending the list of active games to {}'.format(user.name))
        user.socket.send(msg.encode('utf-8'))
        user.socket.send('CMD$'.encode('utf-8'))

    """
    Send to the asking user a list of the other users present in the Room
    """
    def list_users(self, user):
        msg = 'LISTU '
        for u in self.users:
            if u.name != user.name:
                msg = msg + u.name + ','
        msg = msg + '$'
        print ('Sending the list of users to {}'.format(user.name))
        user.socket.send(msg.encode('utf-8'))
        user.socket.send('CMD$'.encode('utf-8'))

    def handler(self, data, user):
        command = data.decode("utf-8")
        if command == "list games":
            self.list_games(user)
        elif command == "list users":
            self.list_users(user)
        elif command.startswith("join "):
            gameID = command.strip("join ")
            # if gameID != "":
            #     #Appel à join_game(gameID)
        elif command.startswith("nickname "):
            newName = command.strip("nickname")
            if newName != "":
                self.change_username(user, newName)
        elif command.startswith("challenge "):
            opponent = command.strip("challenge ")
            # if opponent != "":
                #Appel à challenge_user()



def start_server():

    HOST = ''
    PORT = 8888
    RECV_BUFFER = 4096

    connection_list = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    connection_list.append(server_socket)

    print('Server {} started on port {}'.format(socket.gethostbyname(socket.gethostname()),
                                                PORT))

    room = Room()

    while True:
        read_sockets, _ , _ = select.select(connection_list, [], [])

        for client in read_sockets:
            if client is server_socket:
                new_socket, addr = server_socket.accept()
                user = User(new_socket,
                            'Guest'+str(random.randint(0,9999)),
                            addr)
                connection_list.append(user)
                room.users.append(user)
                room.instructions(user)
                print ('New connection from {} {} '.format(user.name,
                                                           user.ip))

                # if (len(connection_list) - 1) == 2:
                #     room.games[0].start(connection_list[1], connection_list[2])
                #     room.games[0].send_turn()
                #     print ('New game started \n' \
                #            ' Player 1: {}\n'     \
                #            ' Player 2: {}'.format(room.games[0].players[0].name,
                #                                   room.games[0].players[1].name))

            else:
                data = client.socket.recv(RECV_BUFFER)
                if data:
                    for user in room.users:
                        if client == user :
                            room.handler(data, client)

                    for game in room.games:
                        for player in game.players:
                            if client is player:
                                print('Received data from {}'.format(client.name))
                                game.handler(client, data)

                else:
                    print ('Client {} ({}) disconnected'.format(client.name,
                                                                client.ip))
                    connection_list.remove(client)
                    client.socket.close()

if __name__ == '__main__':
    sys.exit(start_server())
