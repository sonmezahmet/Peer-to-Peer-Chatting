import socket
import threading
import select
import time
import logging
from message_tcp import MessageTCP
from peer_client import PeerClient
from peer_server import PeerServer


class Client:
    def __init__(self, server_tcp_port, server_udp_port):
        self.server_ip = "localhost"
        self.server_tcp_port = server_tcp_port
        self.server_udp_port = server_udp_port

        # Create TCP socket and connect to the server
        self.client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_tcp.connect((self.server_ip, self.server_tcp_port))
        logging.info("TCP socket has created and connected to the registry server.")
        # print("TCP socket has created and connected to the registry server.")

        # Create UDP socket for sending 'HELLO' messages to the server
        self.client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # print("UDP socket has created.")
        logging.info("UDP socket has created.")
        # Credentials of the this client
        self.login_credentials = (None, None)
        # Online status of this client
        self.is_online = False
        # Peer server port number of this client
        self.peer_server_port = None
        # Peer server of this client
        self.peer_server = None
        # Peer client of this client
        self.peer_client = None
        # Timer for sending 'HELLO' messages
        self.timer = None

        choice = "0"
        while choice != "3":
            if not self.is_online:
                # Show menu to the client (1: Create A Account, 2: Login)
                choice = input("1: Create Account\n2: Login\n")
                if choice == "1":
                    self.__CreateAccount()
                elif choice == "2":
                    self.__Login()
            else:
                # Show menu to the client (1: Search, 2: Start Chat, 3: Logout)
                choice = input("1: Search\n2: Start Chat\n3: Logout\n")
                if choice == "1":
                    # Get username to be searched from the client
                    username = input("Username to be searched: ")
                    self.__Search(username)
                elif choice == "2":
                    self.__StartChat()

                elif choice == "3":
                    self.__Logout()

                # Chat request is accepted
                elif choice == "A":
                    msg = MessageTCP.CreateMessage("CHAT_REQ_RESP", "ACCEPT")
                    self.peer_server.connected_peer_socket.send(msg)
                    # print(f'\'{msg.decode("utf-8")}\' is sent to the connected peer')
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the connected peer'
                    )
                    # Connect to the peer's server for sending messages
                    self.peer_client = PeerClient(
                        self.login_credentials[0],
                        "localhost",
                        int(self.peer_server.connected_peer_port),
                        self.peer_server,
                        True,
                    )
                    self.peer_client.start()
                    self.peer_client.join()
                elif choice == "R":
                    msg = MessageTCP.CreateMessage("CHAT_REQ_RESP", "REJECT")
                    self.peer_server.connected_peer_socket.send(msg)
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the connected peer'
                    )
                    # print(f'\'{msg.decode("utf-8")}\' is sent to the connected peer')
                    self.peer_server.is_chat_requested = False
                    self.peer_server.sockets.remove(
                        self.peer_server.connected_peer_socket
                    )

    def __CreateAccount(self):
        username = ""
        password = ""
        # Get username and password from the client
        while username == "" or password == "":
            username = input("Username: ")
            password = input("Password: ")

        # Send credentials to the registry server
        msg = MessageTCP.CreateMessage("REG", f"{username} {password}")
        self.client_tcp.send(msg)
        logging.info(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')
        # print(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')

        # Get response message from the registry server
        msg_header, msg_command, payload = self.__GetTcpMessage()
        logging.info(f"'{msg_header} {payload}' is received from the registry server.")
        # print(f"'{msg_header} {payload}' is received from the registry server.")

        if msg_command == "REG_RESP":
            # If the register process is successful then enter here
            if payload == "OK":
                logging.info("Register process is successful.")
                # print("Register process is successful.")

                # Set user credentials
                self.login_credentials = (username, password)
                self.is_online = True

                # Start sending 'HELLO' messages to the registry server
                self.__SendHelloMessage()

                # Get peer server port from the user
                port = ""
                while port == "":
                    port = input("Please enter your peer server port: ")
                    try:
                        port = int(port)
                    except ValueError as valEr:
                        logging.error("ValueError: {0}".format(valEr))  # to-do
                        print("Please enter a integer.")
                        port = ""
                        continue

                    # Send it to the registry server
                    msg = MessageTCP.CreateMessage("PS_PORT", f"{port}")
                    self.client_tcp.send(msg)
                    # print(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the registry server.'
                    )
                    # Get response message from the registry server
                    msg_header, msg_command, payload = self.__GetTcpMessage()
                    # print(f"'{msg_header} {payload}' is received from the registry server.")
                    logging.info(
                        f"'{msg_header} {payload}' is received from the registry server."
                    )

                    if msg_command == "PS_PORT_RESP":
                        if payload == "OK":
                            self.peer_server_port = port
                            # print(f"Peer server port of this client is {self.peer_server_port}.")
                            logging.info(
                                f"Peer server port of this client is {self.peer_server_port}."
                            )
                        elif payload == "FAIL":
                            logging.error("FAIL wrong port number")
                            print(
                                "The port you have entered is already used by another client."
                            )
                            print("Please enter a different port number")
                            print("The entered peer server port number is invalid.")
                            port = ""
                            continue

                # Create peer server of this client
                self.peer_server = PeerServer(
                    self.login_credentials[0], self.peer_server_port
                )
                self.peer_server.start()

            # If the registry process is failed then enter here
            elif payload == "FAIL":
                logging.error(
                    "FAIL The register process is failed (The username is already in use)."
                )
                print(
                    "The register process is failed (The username is already in use)."
                )
                print("The username is already in use.")

    def __Login(self):
        username = ""
        password = ""
        # Get username and password from the client
        while username == "" or password == "":
            username = input("Username: ")
            password = input("Password: ")

        # Send credentials to the registry server
        msg = MessageTCP.CreateMessage("LOG", f"{username} {password}")
        self.client_tcp.send(msg)
        logging.info(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')
        # print(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')

        # Get response message from the registry server
        msg_header, msg_command, payload = self.__GetTcpMessage()
        logging.info(f"'{msg_header} {payload}' is received from the registry server.")
        # print(f"'{msg_header} {payload}' is received from the registry server.")

        if msg_command == "LOG_RESP":
            # If the register process is successful then enter here
            if payload == "OK":
                print("Login process is successful.")
                logging.info("Login process is successful.")
                # Set user credentials
                self.login_credentials = (username, password)
                self.is_online = True

                # Start sending 'HELLO' messages to the registry server
                self.__SendHelloMessage()

                # Get peer server port from the user
                port = ""
                while port == "":
                    port = input("Please enter your peer server port: ")
                    try:
                        port = int(port)
                    except ValueError as valEr:
                        logging.error("ValueError: {0}".format(valEr))  # to-do
                        print("Please enter a integer.")
                        port = ""
                        continue

                    # Send it to the registry server
                    msg = MessageTCP.CreateMessage("PS_PORT", f"{port}")
                    self.client_tcp.send(msg)
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the registry server.'
                    )
                    # print(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')

                    # Get response message from the registry server
                    msg_header, msg_command, payload = self.__GetTcpMessage()
                    # print(f"'{msg_header} {payload}' is received from the registry server.")
                    logging.info(
                        f"'{msg_header} {payload}' is received from the registry server."
                    )
                    if msg_command == "PS_PORT_RESP":
                        if payload == "OK":
                            self.peer_server_port = port
                            logging.info(
                                f"Peer server port of this client is {self.peer_server_port}."
                            )
                            # print(f"Peer server port of this client is {self.peer_server_port}.")
                        elif payload == "FAIL":
                            logging.error(
                                "FAIL The port you have entered is already used by another client."
                            )
                            print(
                                "The port you have entered is already used by another client."
                            )
                            print("Please enter a different port number")
                            print("The entered peer server port number is invalid.")
                            port = ""
                            continue

                # Create peer server of this client
                self.peer_server = PeerServer(
                    self.login_credentials[0], self.peer_server_port
                )
                self.peer_server.start()

            # If the login process is failed then enter here
            elif payload == "FAIL":
                logging.error(
                    "FAIL The login process is failed (Wrong username or password)."
                )
                print("The login process is failed (Wrong username or password).")
                print("Wrong username or password.")

    def __Search(self, username):
        # Send request to the registry server
        msg = MessageTCP.CreateMessage("SEARCH", f"{username}")
        self.client_tcp.send(msg)

        # Get response from the registry server
        msg_header, msg_command, payload = self.__GetTcpMessage()

        if msg_command == "SEARCH_RESP":
            if payload == "OFFLINE":
                logging.info(f"{username} is offline.")
                print(f"{username} is offline.")
            elif payload == "NOT_FOUND":
                logging.info(f"{username} is not found.")
                print(f"{username} is not found.")
            else:
                payload = payload.split(" ")
                logging.info(f"{username} is online.")
                print(f"{username} is online.")
                logging.info(f"Contact address is {payload[0]}:{payload[1]}")
                # print(f"Contact address is {payload[0]}:{payload[1]}")
                return payload[0], payload[1]
        return None, None

    def __StartChat(self):
        # Get username for chatting
        username = input("Who do you want to chat? ")

        # Send request to the registry server and get response
        peer_ip, peer_port = self.__Search(username)

        if peer_port is not None:
            # Connect to peer's server
            self.peer_client = PeerClient(
                self.login_credentials[0],
                peer_ip,
                int(peer_port),
                self.peer_server,
                False,
            )
            self.peer_client.start()
            self.peer_client.join()

    def __Logout(self):
        # Send logout message to the registry server
        msg = MessageTCP.CreateMessage("LOGOUT", "")
        self.client_tcp.send(msg)
        # print(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')
        logging.info(f'\'{msg.decode("utf-8")}\' is sent to the registry server.')
        self.timer.cancel()
        self.client_tcp.close()
        self.client_udp.close()

    def __GetTcpMessage(self):
        # Receive msg header
        msg_header = self.client_tcp.recv(25).decode("utf-8")

        # Unpack message header
        msg_size, msg_command = MessageTCP.UnpackMessageHeader(msg_header)

        # Receive payload
        payload = self.client_tcp.recv(msg_size).decode("utf-8")

        return msg_header, msg_command, payload

    def __SendHelloMessage(self):
        msg = f"HELLO {self.login_credentials[0]}".encode("utf-8")
        self.client_udp.sendto(msg, (self.server_ip, self.server_udp_port))
        self.timer = threading.Timer(6, self.__SendHelloMessage)
        self.timer.start()


# Initialize logging
logging.basicConfig(filename="client.log", level=logging.INFO)
client = Client(1235, 4322)
