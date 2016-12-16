import socket, select
import re
import sys

from grid import *

def init_grids():
    return Grid(), Grid(), Grid()

def start_server():

    HOST = ''
    PORT = 8888
    RECV_BUFFER = 4096

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
                print ('Client {0} connected'.format(ip))


            else:
                data = sock.recv(RECV_BUFFER)
                if data:
                    print('Received data from client')
                else:
                    print ('Client {0} diconnected'.format(socket.gethostname()))
                    readers_list.remove(sock)
                    sock.close()

if __name__ == '__main__':
    sys.exit(start_server())
