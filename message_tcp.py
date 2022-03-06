import socket

HEADER_SIZE_LENGTH = 10
HEADER_COMMAND_LENGTH = 15


class MessageTCP:
    @staticmethod
    def CreateMessage(command, data):
        msg_size = len(data.encode('utf-8'))
        msg_header = f'{msg_size:<{HEADER_SIZE_LENGTH}}{command:<{HEADER_COMMAND_LENGTH}}'
        msg = msg_header + data
        return msg.encode('utf-8')

    @staticmethod
    def UnpackMessageHeader(msg_header):
        msg_size = int(msg_header[:HEADER_SIZE_LENGTH])
        msg_command = msg_header[HEADER_SIZE_LENGTH:].strip()
        return msg_size, msg_command

