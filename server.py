import socket
import threading
import select
import logging
from message_tcp import MessageTCP


class ClientThread(threading.Thread):
    def __init__(self, ip, port, client_socket):
        threading.Thread.__init__(self)

        self.ip = ip
        self.port = port
        self.client_socket = client_socket

        self.username = None
        self.is_online = True
        self.udp_server = None

        self.lock = threading.Lock()
        logging.info(f"New client thread started for {self.ip}:{self.port}")

    def run(self):

        logging.info(f"{self.ip}:{self.port} has connected.")
        while True:
            try:
                msg_header, msg_command, payload = self.__GetTcpMessage()
                dest = (
                    f"{self.ip}:{self.port}" if self.username is None else self.username
                )

                logging.info(f"'{msg_header} {payload}' is received from {dest}")
                if msg_command == "LOG":
                    self.__Login(payload)
                elif msg_command == "REG":
                    self.__Register(payload)
                elif msg_command == "SEARCH":
                    self.__Search(payload)
                elif msg_command == "LOGOUT":
                    self.__Logout()
                    break

            except Exception as e:
                pass

    def __Login(self, payload):
        payload = payload.split(" ")
        username = payload[0]
        password = payload[1]

        # Check credentials
        is_credential_true = False
        with open("user_infos.txt", "r") as f:
            credentials = f.read().split("\n")
            for user in credentials:
                if user == "":
                    continue
                credential_user = user.split(" ")
                user_username = credential_user[0]
                user_password = credential_user[1]
                if username == user_username and password == user_password:
                    self.username = user_username
                    logging.info(f"{self.ip}:{self.port} is {self.username}.")
                    is_credential_true = True
                    break

        if is_credential_true:
            # Send response to the client
            msg = MessageTCP.CreateMessage("LOG_RESP", f"OK")
            self.client_socket.send(msg)
            logging.info(f'\'{msg.decode("utf-8")}\' sent to the {self.username}.')

            self.lock.acquire()
            try:
                tcp_threads[self.username] = self
            finally:
                self.lock.release()

            # Create UDP server for this client
            self.udp_server = UDPServer(self.username, self.client_socket)
            self.udp_server.start()
            self.udp_server.timer.start()
            logging.info(
                f"UDP server for {self.username} has created and started to listening."
            )

            # Remove from the offline list
            offline_users.remove(self.username)

            # Add it to the online users
            online_users[self.client_socket] = [self.username, self.ip, self.port]
            logging.info(f"{self.username} is online now.")

            # Get peer server port from the client
            msg_header, msg_command, payload = self.__GetTcpMessage()
            logging.info(f"'{msg_header} {payload}' is received from {self.username}")

            if msg_command == "PS_PORT":
                # Look other clients peer server port and check uniqueness
                is_port_unique = True
                for user in online_users:
                    port_number = online_users[user][1]
                    if port_number == payload:
                        is_port_unique = False
                        break

                if is_port_unique:
                    # Change port
                    online_users[self.client_socket] = [self.username, self.ip, payload]
                    # Send response to the client
                    msg = MessageTCP.CreateMessage("PS_PORT_RESP", f"OK")
                    self.client_socket.send(msg)
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the {username}.'
                    )
                else:
                    # Send response to the client
                    msg = MessageTCP.CreateMessage("PS_PORT_RESP", f"FAIL")
                    self.client_socket.send(msg)
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the {username}.'
                    )
        else:
            # Send response to the client
            msg = MessageTCP.CreateMessage("REG_RESP", "FAIL")
            self.client_socket.send(msg)
            logging.info(
                f'\'{msg.decode("utf-8")}\' is sent to the {self.ip}:{self.port}.'
            )

    def __Register(self, payload):
        payload = payload.split(" ")
        username = payload[0]
        password = payload[1]

        # Check credentials for uniqueness of entered username
        is_username_unique = True
        with open("user_infos.txt", "r") as f:
            credentials = f.read().split("\n")
            for user in credentials:
                if user == "":
                    continue
                credential_user = user.split(" ")
                user_username = credential_user[0]
                if username == user_username:
                    is_username_unique = False
                    break

        if is_username_unique:
            self.username = username
            print(f"{self.ip}:{self.port} is {self.username}.")

            self.lock.acquire()
            try:
                tcp_threads[self.username] = self
            finally:
                self.lock.release()

            # Create UDP server for this client
            self.udp_server = UDPServer(self.username, self.client_socket)
            self.udp_server.start()
            self.udp_server.timer.start()
            logging.info(
                f"UDP server for {self.username} has created and started to listening."
            )

            # Send response to the client
            msg = MessageTCP.CreateMessage("REG_RESP", f"OK")
            self.client_socket.send(msg)
            logging.info(f'\'{msg.decode("utf-8")}\' is sent to the {username}.')

            # Add new entry to user_infos.txt
            with open("user_infos.txt", "a") as f:
                f.write(f"{username} {password}\n")
            logging.info(f"{username} is added to the registry database.")

            # Add it to the online users
            online_users[self.client_socket] = [self.username, self.ip, self.port]
            logging.info(f"{self.username} is online now.")

            # Get peer server port from the client
            msg_header, msg_command, payload = self.__GetTcpMessage()

            logging.info(f"'{msg_header} {payload}' is received from {self.username}")
            if msg_command == "PS_PORT":
                # Look other clients peer server port and check uniqueness
                is_port_unique = True
                for user in online_users:
                    port_number = online_users[user][2]
                    if port_number == payload:
                        is_port_unique = False
                        break

                if is_port_unique:
                    # Change port
                    online_users[self.client_socket] = [self.username, self.ip, payload]
                    # Send response to the client
                    msg = MessageTCP.CreateMessage("PS_PORT_RESP", f"OK")
                    self.client_socket.send(msg)
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the {username}.'
                    )
                else:
                    # Send response to the client
                    msg = MessageTCP.CreateMessage("PS_PORT_RESP", f"FAIL")
                    self.client_socket.send(msg)
                    logging.info(
                        f'\'{msg.decode("utf-8")}\' is sent to the {username}.'
                    )

        else:
            # Send response to the client
            msg = MessageTCP.CreateMessage("REG_RESP", "FAIL")
            self.client_socket.send(msg)
            logging.info(
                f'\'{msg.decode("utf-8")}\' is sent to the {self.ip}:{self.port}.'
            )

    def __Search(self, payload):
        username_to_be_search = payload
        is_user_found = False
        # Search username in online users
        for user_socket in online_users:
            user_username = online_users[user_socket][0]
            user_ip = online_users[user_socket][1]
            user_port = online_users[user_socket][2]
            if user_username == username_to_be_search:
                msg = MessageTCP.CreateMessage("SEARCH_RESP", f"{user_ip} {user_port}")
                is_user_found = True
                break

        if not is_user_found:
            # Look offline list
            if username_to_be_search in offline_users:
                msg = MessageTCP.CreateMessage("SEARCH_RESP", "OFFLINE")
            else:
                # User not found
                msg = MessageTCP.CreateMessage("SEARCH_RESP", "NOT_FOUND")

        # Send response
        self.client_socket.send(msg)
        logging.info(f'\'{msg.decode("utf-8")}\' is sent to the {self.ip}:{self.port}.')

    def __Logout(self):
        # Delete thread, remove client from the online users and add it to the offline users
        self.lock.acquire()
        try:
            del online_users[self.client_socket]
            del tcp_threads[self.username]
            offline_users.append(self.username)
        finally:
            self.lock.release

        logging.info(f"{self.username} has logged out!")
        self.client_socket.close()
        self.udp_server.timer.close()

    def __GetTcpMessage(self):
        # Receive msg header
        msg_header = self.client_socket.recv(25).decode("utf-8")

        # Unpack message header
        msg_size, msg_command = MessageTCP.UnpackMessageHeader(msg_header)

        # Receive payload
        payload = self.client_socket.recv(msg_size).decode("utf-8")

        return msg_header, msg_command, payload

    def ResetUDPTimer(self):
        self.udp_server.ResetTimer()


class UDPServer(threading.Thread):
    def __init__(self, username, client_socket):
        threading.Thread.__init__(self)
        self.username = username
        # timer thread for the udp server is initialized
        self.timer = threading.Timer(3, self.WaitHelloMessage)
        self.client_socket_tcp = client_socket

    # if hello message is not received before timeout
    # then peer is disconnected
    def WaitHelloMessage(self):
        logging.info("Wait Hello Message")
        if self.username is not None:
            # make user offline
            offline_users.append(self.username)
            if self.username in tcp_threads:
                del tcp_threads[self.username]
        self.client_socket_tcp.close()
        logging.info("Removed " + self.username + " from online peers")

    # resets the timer for udp server
    def ResetTimer(self):
        self.timer.cancel()
        self.timer = threading.Timer(10, self.WaitHelloMessage)
        self.timer.start()


# Initialize logger
logging.basicConfig(filename="server.log", level=logging.INFO)
logging.info("Server is started.")
ip = "localhost"
tcp_port = 1235
udp_port = 4322

online_users = {}
offline_users = []
tcp_threads = {}

# Get offline users
with open("user_infos.txt", "r") as f:
    users = f.read().split("\n")
    for user in users:
        user_username = user.split(" ")[0]
        offline_users.append(user_username)

logging.info("Offline users added.")


# Create TCP socket
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.bind((ip, tcp_port))
tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_socket.listen()
logging.info("TCP socket has created and started to listening incoming connections.")


# Create UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((ip, udp_port))

logging.info("UDP socket has created for receiving 'HELLO' messages.")
sockets = [tcp_socket, udp_socket]

while sockets:
    rlist, wlist, _ = select.select(sockets, [], [])

    for socket in rlist:
        if socket is tcp_socket:
            # Accept connection and create client thread
            client_socket, client_address = tcp_socket.accept()

            logging.info(
                f"{client_address[0]}:{client_address[1]} has connected to the registry server."
            )
            client_thread = ClientThread(
                client_address[0], client_address[1], client_socket
            )
            client_thread.start()

        elif socket is udp_socket:
            msg, client_address = socket.recvfrom(1024)
            msg = msg.decode("utf-8").split(" ")

            if msg[0] == "HELLO":
                if msg[1] in tcp_threads:
                    logging.info(f"'{msg[0]}' is received from {msg[1]}")
                    tcp_threads[msg[1]].ResetUDPTimer()
