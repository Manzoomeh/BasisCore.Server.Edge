import socket

from listener.message_type import MessageType


class Message:
    def __init__(self, sessionId: str,  messageType: MessageType, buffer: bytes = None) -> None:
        self.session_id = sessionId
        self.type = messageType
        self.buffer = buffer

    def write(self, connection: socket.socket) -> None:
        connection.send(self.type.value.to_bytes(1, 'big'))
        data = self.session_id.encode()
        data_length_bytes = len(data).to_bytes(4, 'big')
        connection.send(data_length_bytes)
        connection.send(data)

        if self.type != MessageType.disconnect:
            data_length_bytes = len(self.buffer).to_bytes(4, 'big')
            connection.send(data_length_bytes)
            connection.send(self.buffer)

    @staticmethod
    def create_add_hock(session_id: str, buffer: bytes):
        return Message(session_id, MessageType.ad_hock, buffer)

    @staticmethod
    def read(connection: socket.socket):
        message: Message = None
        data = connection.recv(1)
        if data:
            message_type = int.from_bytes(data, byteorder='big', signed=True)
            data = connection.recv(4)
            data_len = int.from_bytes(data, byteorder='big', signed=True)
            data = connection.recv(data_len)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type != 3:
                data = connection.recv(4)
                data_len = int.from_bytes(data, byteorder='big', signed=True)
                data = connection.recv(data_len)
                parameter = data
            message = Message(
                session_id, MessageType(message_type), parameter)
        return message
