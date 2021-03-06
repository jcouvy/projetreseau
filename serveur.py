# -*- coding: utf-8 -*-
#!/usr/bin/python3

import socket, select
import sys
import random

from threading import Thread, Timer
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
        self.gameId = gameId
        self.players = [None, None]
        self.observators = []
        self.grids = [Grid(), Grid(), Grid()]
        self.turn = -1

    """
    Appends the observator to the players array of the game and removes it from
    the observators. Starts the game is both slots are filled and broadcast a msg
    to everyone in the game.
    """
    def playing(self, observator):
        if self.players[P1] != None and self.players[P2] != None:
            observator.socket.send(b'MSG Partie en cours$')
            return

        for i in range(2):
            if self.players[i] == None:
                # Append the client to the player array and remove it from
                # the observators.
                self.players[i] = observator
                self.observators.remove(observator)
                if self.players[P1] != None and self.players[P2] != None:
                    msg = 'MSG La partie commence !\n Joueur 1 - '+self.players[P1].name+' O\n Joueur 2 - '+self.players[P2].name+' X\n$'
                    self.players[P1].socket.send(msg.encode('utf-8'))
                    self.players[P2].socket.send(msg.encode('utf-8'))
                    self.broadcast_obs(msg.encode('utf-8'))
                    self.broadcast_obs(self.encode_grid(self.grids[OBS]))
                    self.start()
                    return
                observator.socket.send(b'MSG En attente d\'un adversaire...$')
                return


    """
    Fills the Game structure and sends a byte message encoding each player's grid.
    The first turn is chosen with a pseudo random coin-flip.
    """
    def start(self):
        self.turn = random.randint(1,2)
        self.players[P1].socket.send(b'GRID 000000000$')
        self.players[P2].socket.send(b'GRID 000000000$')
        self.send_turn()

    """
    Send the next turn in a byte-string to each player.
    """
    def send_turn(self):
        assert(self.turn == J1 or self.turn == J2)
        if self.turn == J1:
            self.players[P1].socket.send(b'PLAY$')
            self.players[P2].socket.send(b'WAIT$')
            self.broadcast_obs('MSG Au tour du Joueur 1$'.encode('utf-8'))
        else:
            self.players[P1].socket.send(b'WAIT$')
            self.players[P2].socket.send(b'PLAY$')
            self.broadcast_obs('MSG Au tour du Joueur 2$'.encode('utf-8'))

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
    This function decodes the observator input. Allows the observator to start a game,
    or allows him to quit the game.
    """
    def obs_handler(self, observator, data):
        command = data.decode("utf-8")
        print(command)
        if command == "play":
            self.playing(observator)
        #elif command is "quit":
        else:
            observator.socket.send(b'MSG Commande inconnue$')
            observator.socket.send(b'CMD$')


    """
    Decodes the player's move, modifies the according Grid, sends the encoded grid
    back and then updates the turn. Exceptions are raised in order to prevent the server
    from stopping if any player tries an invalid move (i.e: Grid.play() assert fails).
    The player is asked to play again if any exception is caught.
    """
    def player_handler(self, player, data):
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
                    obs.socket.send(self.encode_grid(0))

                self.turn = enemy

                if self.game_over() == -1:
                    self.send_turn()
                else:
                    self.end_game()
                print ('Sending encoded grid to {}'.format(player.name))

    """
    Broadcast the message parsed in parameter (must be encoded in utf-8) to
    every observator of the game
    """
    def broadcast_obs(self, msg):
        for obs in self.observators:
            obs.socket.send(msg)
    """
    Checks if the game is over (if a win condition is found on the global Grid).
    Send a byte-string to each players according to the output of the game.
    """
    def game_over(self):
        state = self.grids[OBS].gameOver()
        if state == EMPTY:
            self.players[P1].socket.send(b'DRAW$')
            self.players[P2].socket.send(b'DRAW$')
            self.broadcast_obs(b'DRAW$')
        if state == J1:
            self.players[P1].socket.send(b'WIN$')
            self.players[P2].socket.send(b'LOSE$')
            msg = 'MSG '+self.players[P1].name+' remporte la partie$'
            self.broadcast_obs(msg.encode('utf-8'))
        if state == J2:
            self.players[P1].socket.send(b'LOSE$')
            self.players[P2].socket.send(b'WIN$')
            msg = 'MSG '+self.players[P2].name+' remporte la partie$'
            self.broadcast_obs(msg.encode('utf-8'))
        return state


    """
    This function is called when a game is over, changes players into observators,
    and give them a prompt to enter observators commands.
    """
    def end_game(self):
        end_msg = "Vous avez été replacé parmi les observateurs, entrez la commande <play> pour pouvoir rejouer."

        self.observators.append(self.players[P1])
        self.players[P1].socket.send(bytearray("MSG " + end_msg + "$", "utf-8"))
        self.players[P1].socket.send(b'CMD$')
        self.players[P1] = None

        self.observators.append(self.players[P2])
        self.players[P2].socket.send(bytearray("MSG " + end_msg + "$", "utf-8"))
        self.players[P2].socket.send(b'CMD$')
        self.players[P2] = None

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
        self.users = []

    """
    Send information parsed in param to every users
    """
    def broadcast_all(self, data):
        msg = 'MSG ' + data + '$'
        print(msg)
        for user in self.users:
            user.socket.send(msg.encode('utf-8'))

    """
    Appends the user to the observator list of the game named gameId
    """
    def join_game(self, user, gameId):
        for game in self.games:
            if game.gameId == gameId:
                print('APPEND {} TO :'.format(user.name))
                print(game.observators)
                game.observators.append(user)
                print(game.observators)
                join_msg = "MSG Vous venez de rejoindre la partie : " + gameId + "\n" \
                + "Entrez la commande <play> pour pouvoir jouer$"
                user.socket.send(bytearray(join_msg, "utf-8"))
                if game.players[P1] and game.players[P2]:
                    join_msg = 'MSG Une partie est en cours:\n' \
                    + ' - Joueur 1: ' + game.players[P1].name + ' ' + symbols[J1] + '\n'\
                    + ' - Joueur 2: ' + game.players[P2].name + ' ' + symbols[J2] + '$'
                    user.socket.send(join_msg.encode('utf-8'))
                    user.socket.send(game.encode_grid(game.grids[OBS]))
                user.socket.send(b'CMD$')
        # Removing the user from the Room
        print ('Removing {} from Room\'s userlist'.format(user.name))
        self.users.remove(user)

    """
    Send the set of available commands to every users in the Room
    """
    def instructions(self, user):
        msg = "Liste des commandes disponibles:\n\
        - join <game id>  (observer une partie en cours)\n\
        - list games (lister les games)\n\
        - list users\n\
        - nickname <name> (choisir un pseudo)\n"
        user.socket.send(bytearray("MSG " + msg + "$", "utf-8"))
        user.socket.send('CMD$'.encode('utf-8'))

    """
    Changes the user's name with newName and informs the other users
    """
    def change_username(self, user, newName):
        oldName = user.name
        for u in self.users:
            if u.name == oldName:
                u.name = newName
        print ('Client {} renamed {}'.format(oldName, newName))
        self.broadcast_all(oldName+' a été renommé en '+newName)
        user.socket.send('CMD$'.encode('utf-8'))

    """
    Send to the user the list of ongoing/empty games
    """
    def list_games(self, user):
        msg = 'LISTG '
        for game in self.games:
            if game.players[P1] != None and game.players[P2] != None:
                msg = msg + game.gameId + ','
        msg = msg + ";"
        for game in self.games:
            if game.players[P1] == None and game.players[P2] == None:
                msg = msg + game.gameId + ','
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


    """
    Handles the messages coming from users in the Room, and then call the appropriate function.
    """
    def handler(self, user, data):
        command = data.decode("utf-8")
        if command == "list games":
            self.list_games(user)
        elif command == "list users":
            self.list_users(user)
        elif command.startswith("join "):
            gameId = command.replace("join ", "")
            for game in self.games:
                if gameId == game.gameId:
                    self.join_game(user, gameId)
                    return
            user.socket.send('MSG Nom de partie inconnu !$'.encode('utf-8'))
            user.socket.send('CMD$'.encode('utf-8'))
        elif command.startswith("nickname "):
            newName = command.replace("nickname ", "")
            if newName != "":
                self.change_username(user, newName)
        else:
            user.socket.send('MSG Commande Inconnue !$'.encode('utf-8'))
            user.socket.send('CMD$'.encode('utf-8'))

"""
There are three different handlers for each client's type:
class Game - observator (watching a game)
class Game - player (playing in a game)
class Room - user (not in any game)
Each handler is called by the server depending on the socket type
"""
def pick_handler(room, client, data):
    for user in room.users:
        if client is user :
            room.handler(client, data)
            return

    for game in room.games:
        for player in game.players:
            if client is player:
                print('Received data from {}'.format(client.name))
                game.player_handler(client, data)
                return
        for obs in game.observators:
            if client is obs:
                print('Received data from {}'.format(client.name))
                game.obs_handler(client, data)


"""
Automatically declares the remaining player as winner if his opponent doesn't
reconnect in time.
"""
def forfeit(game):
    for player in game.players:
        if player:
            game.observators.append(player)
            game.players[P1] = None
            game.players[P2] = None
    msg = 'MSG Vous avez gagné par forfait$'
    player.socket.send(msg.encode('utf-8'))
    msg = 'MSG Vous avez été replacé parmi les observateurs, entrez la commande <play> pour pouvoir rejouer.$'
    player.socket.send(msg.encode('utf-8'))
    player.socket.send(b'CMD$')

"""
If the timer runs out:
Resets the timer to None, forfeits the game and remove the user from the
pending list.

reconnection_list is a list of 3-tuples:
(game ID, client IP, player n°)
"""
def timeout(reconnection_list, game):
    disconnection_timer = None
    forfeit(game)
    for element in reconnection_list:
        if element[0] == game.gameId:
            reconnection_list.remove(element)
            print("{} timed out".format(element[1]))

"""
Starts a TCP server on port 8888 accepting IPv4 connections.
The server starts a single Room that hosts multiple game lobbies. When
connecting, a user is appended to the Room's user list and managed according to
his status (user, player, obs). If the user was in the reconnection list, then
he will be connected back to his game, and the game will continue.

This function handles disconnections too. If a room's user or an observator
is disconnected, then the server just close the socket.
But if it's a player that is disconnected, then the server adds the player in the
reconnection list, and starts a timer.
If the disconnected player is not able to reconnect on time, then the other player wins by forfeit
and is placed among the other observators.
"""
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
    disconnection_timer = None
    reconnection_list = []
    need_to_be_reconnected = None

    while True:
        read_sockets, _ , _ = select.select(connection_list, [], [])

        for client in read_sockets:
            if client is server_socket:
                new_socket, addr = server_socket.accept()
                user = User(new_socket,
                            'Guest'+str(random.randint(0,9999)),
                            addr[0])

                need_to_be_reconnected = False
                # reco list : [game ID, client IP, P1/P2]
                for element in reconnection_list:
                    if user.ip == element[1]:
                        if disconnection_timer != None and disconnection_timer.isAlive:
                            need_to_be_reconnected = True
                            disconnection_timer.cancel()
                            disconnection_timer = None

                            for game in room.games:
                                if game.gameId == element[0]:
                                    game.players[element[2]] = user
                                    user.socket.send(game.encode_grid(element[2]+1))
                                    game.send_turn()

                            reconnection_list.remove(element)

                connection_list.append(user)

                if not need_to_be_reconnected:
                    room.users.append(user)
                    room.instructions(user)
                    print ('New connection from {} {} '.format(user.name,
                                                               user.ip))

            else:
                data = client.socket.recv(RECV_BUFFER)
                if data:
                    pick_handler(room, client, data)
                else:
                    print ('Client {} ({}) disconnected'.format(client.name,
                                                                client.ip))
                    for user in room.users:
                        if client is user:
                            room.users.remove(client)
                    for game in room.games:
                        for obs in game.observators:
                            if client is obs:
                                game.observators.remove(obs)
                        for player in game.players:
                            if client is player:
                                for i in range(2):
                                    if client is game.players[i]:
                                        enemy = P1 if i == P2 else P2
                                        game.players[i] = None
                                        reconnection_list.append((game.gameId, client.ip, i))
                                        disconnection_timer = Timer(20.0, timeout, args=(reconnection_list, game,))
                                        disconnection_timer.start()
                                        disconnection_msg = "MSG Votre adversaire s'est déconnecté... Veuillez patienter.$"
                                        game.players[enemy].socket.send(bytearray(disconnection_msg, "utf-8"))

                    connection_list.remove(client)
                    client.socket.close()


if __name__ == '__main__':
    sys.exit(start_server())
