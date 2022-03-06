import threading
import socket
from message_tcp import MessageTCP
import logging


class PeerClient(threading.Thread):
    def __init__(self, username, connect_ip, connect_port, peer_server, flag):
        threading.Thread.__init__(self)

        self.username = username
        self.connect_ip = connect_ip
        self.connect_port = connect_port
        self.peer_server = peer_server
        self.flag = flag
        logging.basicConfig(filename="client.log", level=logging.INFO)
        self.peer_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # print("Peer client socket is created")
        logging.getLogger("PeerClient:").info("Peer client socket is created")

    def run(self):
        logging.getLogger("PeerClient:").info("Peer client started.")
        # print("Peer client started.")
        # Connect to server of other peer
        self.peer_client_socket.connect((self.connect_ip, self.connect_port))

        if self.flag is False:
            # Send request message
            msg = MessageTCP.CreateMessage(
                "CHAT_REQ", f"{self.username} {self.peer_server.peer_server_port}"
            )
            self.peer_client_socket.send(msg)
            # print(f"'{msg}' sent to peer server.")
            logging.getLogger("PeerClient:").info(f"'{msg}' sent to peer server.")
            # Get response
            msg_header = self.peer_client_socket.recv(25).decode("utf-8")
            msg_size, msg_command = MessageTCP.UnpackMessageHeader(msg_header)
            payload = self.peer_client_socket.recv(msg_size).decode("utf-8")
            # print(f"Received message: {msg_header} {payload}")
            logging.getLogger("PeerClient:").info(
                f"Received message: {msg_header} {payload}"
            )
            if msg_command == "CHAT_REQ_RESP":
                if payload == "ACCEPT":
                    while True:
                        # Send message to the peer server
                        message = input(">> ")
                        msg = MessageTCP.CreateMessage("MSG", message)
                        self.peer_client_socket.send(msg)
                        # print(f"'{msg}' sent to peer server.")
                        logging.getLogger("PeerClient:").info(
                            f"'{msg}' sent to peer server."
                        )
                elif payload == "BUSY":
                    print("The user is busy now.")
                    self.peer_server.is_chat_requested = False
                    self.peer_client_socket.close()
                elif payload == "REJECT":
                    print("The user rejected your request.")
                    self.peer_server.is_chat_requested = False
                    self.peer_client_socket.close()
        else:
            while True:
                # Send message to the peer server
                message = input(">> ")
                msg = MessageTCP.CreateMessage("MSG", message)
                self.peer_client_socket.send(msg)
