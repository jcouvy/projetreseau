import socket, select
import re
import sys
import random

from grid import *

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

        self.playerOne.send(b'GRID 000000000\n')
        self.playerTwo.send(b'GRID 000000000\n')

    def send_turn(self):
        assert(self.turn == 1 or self.turn == 2)
        if self.turn == 1:
            self.playerOne.send(b'PLAY\n')
            self.playerTwo.send(b'WAIT\n')
        else:
            self.playerOne.send(b'WAIT\n')
            self.playerTwo.send(b'PLAY\n')


def start_server():
    HOST = ''
    PORT = 8888
    RECV_BUFFER = 4096

    USER_DICT = {}
    PLAYER_DICT = {}

    readers_list = []

    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    readers_list.append(server_socket)

    print('Server started on port {0}').format(PORT)

    while True:
        read_socket, _ , _ = select.select(readers_list, [], [])

        for sock in read_socket:

            if sock == server_socket:
                conn, addr = server_socket.accept()
                readers_list.append(conn)
                ip = re.sub(r':*[a-z]*:', '', addr[0])
                USER_DICT.update({str(ip):socket.gethostname()})
                print ('Client {0} ({1}) connected'.format(USER_DICT.get(ip), ip))

                if (len(readers_list) - 1) % 2 == 0:
                    newGame = Game()
                    newGame.start(readers_list[1], readers_list[2])
                    newGame.send_turn()
                    clientA = readers_list[1].getsockname()
                    clientB = readers_list[2].getsockname()
                    clientA_IP = re.sub(r':*[a-z]*:', '', clientA[0])
                    clientB_IP = re.sub(r':*[a-z]*:', '', clientB[0])
                    print ('New game started \n '\
                           'Player 1 - {} ({}) \n '\
                           'Player 2 - {} ({})').format(USER_DICT.get(clientA_IP), clientA_IP,
                                                        USER_DICT.get(clientB_IP), clientB_IP)

            else:
                data = sock.recv(RECV_BUFFER)
                if data:
                        print ('Received data from client')
                else:
                    print ('Client {0} ({1}) disconnect'.format(USER_DICT.get(ip), ip))
                    readers_list.remove(sock)
                    sock.close()


if __name__ == '__main__':
    sys.exit(start_server())
