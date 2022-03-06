import threading
import socket
import select
from message_tcp import MessageTCP
import logging


class PeerServer(threading.Thread):
    def __init__(self, username, peer_server_port):
        threading.Thread.__init__(self)

        self.username = username
        self.peer_server_port = peer_server_port
        logging.basicConfig(filename="client.log", level=logging.INFO)
        self.peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print('Peer server socket is created.')
        logging.getLogger("PeerServer:").info("Peer server socket is created.")
        self.is_chat_requested = False
        self.connected_peer_socket = None
        self.connected_peer_ip = None
        self.connected_peer_port = None
        self.connected_peer_username = None

    def run(self):
        logging.getLogger("PeerServer:").info("Peer server started.")
        # print('Peer server started.')

        # Bind socket and start to listen
        self.peer_server_socket.bind(("localhost", self.peer_server_port))
        self.peer_server_socket.listen()
        # print('Peer server socket has started to the listening.')
        logging.getLogger("PeerServer:").info(
            "Peer server socket has started to the listening."
        )
        self.sockets = [self.peer_server_socket]

        while self.sockets:
            try:
                rlist, wlist, _ = select.select(self.sockets, [], [])

                for socket in rlist:
                    # Accept connected sockets
                    if socket is self.peer_server_socket:
                        (
                            connected_peer_socket,
                            connected_peer_address,
                        ) = self.peer_server_socket.accept()
                        logging.getLogger("PeerServer:").info(
                            f"Peer Server: {connected_peer_address[0]}:{connected_peer_address[1]} is connected."
                        )
                        # print(f'Peer Server: {connected_peer_address[0]}:{connected_peer_address[1]} is connected.')
                        connected_peer_socket.setblocking(0)
                        self.sockets.append(connected_peer_socket)

                        # If there isn't requested for chat to this peer before, make it connected peer
                        if not self.is_chat_requested:
                            self.connected_peer_socket = connected_peer_socket
                            self.connected_peer_ip = connected_peer_address[0]
                            self.connected_peer_port = connected_peer_address[1]
                            self.is_chat_requested = True
                    elif socket is self.connected_peer_socket:
                        # Get message
                        msg_header = socket.recv(25).decode("utf-8")
                        msg_size, msg_command = MessageTCP.UnpackMessageHeader(
                            msg_header
                        )
                        payload = socket.recv(msg_size).decode("utf-8")
                        logging.getLogger("PeerServer:").info(
                            f"'{msg_header} {payload}' is received."
                        )
                        # print(f'\'{msg_header} {payload}\' is received.')

                        if msg_command == "CHAT_REQ":
                            payload = payload.split(" ")
                            username = payload[0]
                            peer_server_port = payload[1]
                            self.connected_peer_port = peer_server_port
                            self.connected_peer_username = username

                            print(f"{username} want to chat with you.")
                            print(f"(A)ccept or (R)eject? ")

                        elif msg_command == "MSG":
                            print(f"Peer: {payload}")
                    else:
                        # Send busy message
                        msg = MessageTCP.CreateMessage("CHAT_REQ_RESP", "BUSY")
                        socket.send(msg)
                        self.sockets.remove(socket)

            except Exception as e:
                pass
