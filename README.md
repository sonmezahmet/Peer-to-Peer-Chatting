# Peer-to-Peer-Chatting

This project about writing P2P chat application with socket programming. It includes two parts which are registry server part and client part. Registry server keeps track of joined clients to the server. With help of registry server clients can chat with each other with using peer to peer approach.

Registry server can do following tasks:
- Account Creation: The client sends ‘REG’ message to the server with a username and a
password. If there is no user with sent username then registry server creates new entry
according to this new user in database.
- Login: The client sends ‘LOG’ message to the server with his/her username and password.
The registry server checks entered credentials whether correct or not by looking database. If credentials are matched then it returns ‘OK’ message to the client and make he/she online. Else it sends ‘FAIL’ message to the client.
- Search: The client sends ‘SEARCH’ message with a username. The registry server looks online users. If searched user is online it returns the contact address of the searched user to the client. If searched user is offline, it returns the ‘OFFLINE’ message to the clients. If searched username not a registered user then registry server returns ‘NOT_FOUND’ message to the client.
- Logout: If the client sends ‘LOGOUT’ message to the registry server then the server close connection with this client. Remove it form online users and add it to the offline users.


Client can do following task:
- Communication with Registry Server: The client sends messages to registry server to achieve
account creation, login, logout, and search operations.
- Chatting with Peer: The client can start chat with another client in the registry server with
using peer to peer approach.

Also when a client connects to the registry server a UDP connection made between client and registry server. Each 60 seconds, client sends ‘HELLO’ messages to the registry server. If registry server can’t receive this ‘HELLO’ message from any particular client, then it close the TCP connection with this client.

## Solution Approach
Firstly we need to define a protocol that is used by clients and registry server. Between registry server and a client there can be 4 different operations which are account creation, login, search for a user and logout. TCP messages’ structures given below.
 <p align='center'><img width="387" alt="Screen Shot 2022-03-06 at 14 46 54" src="https://user-images.githubusercontent.com/56430166/156921646-cf5a5e83-1de2-4534-ad28-274ffdae95dc.png"></p>

### Account Creation:

The client sends a TCP message to the registry server in ‘[Payload Size] [REG] [username password]’ format. The registry server receives this message and firstly looks its database for coming username whether unique or not. If it is unique the registry server creates a message in ‘[Payload Size] [REG_RESP] [OK]’ format and send it to the client. Also it adds new entry its database with this username and password, and add this username to the online users list . If the coming username is not unique, then the registry server sends ‘[Payload Size] [REG_RESP] [FAIL]’ message to the client. <br>
If the client receives ‘[Payload Size] [REG_RESP] [OK]’ message from the registry server, he/she enters peer server port and send it to the registry server in ‘[Payload Size] [PS_PORT] [port_number]’ format. After received this message by registry server, then registry server looks online users’ peer server port numbers and if received port number unique, then it returns ‘[Payload Size] [PS_PORT_RESP] [OK]’ message to the client. If received port number is not unique then it returns ‘[Payload Size] [PS_PORT_RESP] [OK]’ message to the client.
<p align='center'><img width="804" alt="Screen Shot 2022-03-06 at 14 52 01" src="https://user-images.githubusercontent.com/56430166/156921836-f6a57879-673a-41fe-84e9-00adf730ae55.png"></p>

### Login:
The client sends a TCP message to the registry server in ‘[Payload Size] [LOG] [username password]’ format. The registry server receives this message and looks its database for matching received credentials. If match found, it returns ‘[Payload Size] [LOG_RESP] [OK]’ message to the client. Else, it returns ‘[Payload Size] [LOG_RESP] [FAIL]’.<br>
If the client receives ‘[Payload Size] [LOG_RESP] [OK]’ message from the registry server, he/she enters peer server port and send it to the registry server in ‘[Payload Size] [PS_PORT] [port_number]’ format. After received this message by registry server, then registry server looks online users’ peer server port numbers and if received port number unique, then it returns ‘[Payload Size] [PS_PORT_RESP] [OK]’ message to the client. If received port number is not unique then it returns ‘[Payload Size] [PS_PORT_RESP] [OK]’ message to the client.
<p align='center'><img width="804" alt="Screen Shot 2022-03-06 at 14 53 42" src="https://user-images.githubusercontent.com/56430166/156921891-cf946eea-df20-4bd3-b9a7-ad3939990b91.png"></p>

### Search:

The client sends ‘[Payload Size] [SEARCH] [username]’ message to the registry server. Registry server firstly looks online users list with received username. If a match found, it sends ‘[Payload Size] [SEARCH_RESP] [user_ip user_port]’ to the client. Else it looks offline users list. If a match occurs in offline users list then it sends ‘[Payload Size] [SEARCH_RESP] [OFFLINE]’ message to the client. If there isn’t match in offline users, it means user is not exist. So registry server sends ‘[Payload Size] [SEARCH_RESP] [NOT_FOUND]’ message to the client.
<p align='center'><img width="804" alt="Screen Shot 2022-03-06 at 14 55 00" src="https://user-images.githubusercontent.com/56430166/156921940-0a2b2c81-e934-4729-a5d2-d5028ef6eddb.png"></p>

### Logout:
The client sends ‘[Payload Size] [LOGOUT] []’ message to the registry server. Registry server removes this user from online users list and adds it to the offline users list. And closes the connection.
<p align='center'><img width="804" alt="Screen Shot 2022-03-06 at 14 55 55" src="https://user-images.githubusercontent.com/56430166/156921969-793c90e3-6355-4e56-a905-715896c091cc.png"></p>
<br>
After defining client and registry server protocol, now we need to define peer to peer chat protocol between peers.

### Chatting With Peer:
Peer server of each client is created when the client login to the registry server. If client A, want to chat with client B, he/she must send ‘[Payload Size] [SEARCH] [B]’ message to the registry server. If it gets peer_ip and peer_port from the registry server, it creates a peer client socket and connects to the B’s peer server. Then it sends to the chat request to B in ‘[Payload Size] [CHAT_REQ] [A A’s_peer_server_port]’ format.<br>
B’s peer server receives this message from the A and according to his/her choice, he/she sends accept or reject message in ‘[Payload Size] [CHAT_REQ_RESP] [ACCEPT(or REJECT)]’ format. If B is already chatting with another user then he/she sends ‘[Payload Size] [CHAT_REQ_RESP] [BUSY]’ message to the A’s peer server.<br>
After B accepted A’s chat request, they start to chatting. In peer to peer architecture, A’s peer client socket sends messages to the B’s peer server socket and B’s peer client socket sends messages to the A’s peer server socket. Message format is ‘[Payload Size] [MSG] [message]’.
<p align='center'><img width="857" alt="Screen Shot 2022-03-06 at 14 59 07" src="https://user-images.githubusercontent.com/56430166/156922065-a60e9783-333f-4297-b176-4b4b10d815c8.png"></p>

## How to use it?

- Run ‘server.py’ 
- Run ‘client.py’

## Prepared by
- Süleyman Ahmet Sönmez
- Ahmet Turgut
- Fatih Baş
