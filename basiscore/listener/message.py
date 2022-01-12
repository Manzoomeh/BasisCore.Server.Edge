import json
import socket
from typing import Any


from ..listener.message_type import MessageType


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

        if self.type == MessageType.AD_HOC or self.type == MessageType.MESSAGE:
            data_length_bytes = len(self.buffer).to_bytes(4, 'big')
            connection.send(data_length_bytes)
            connection.send(self.buffer)

    @staticmethod
    def create_add_hock(session_id: str, buffer: bytes):
        return Message(session_id, MessageType.AD_HOC, buffer)

    @staticmethod
    def create_disconnect(session_id: str):
        return Message(session_id, MessageType.DISCONNECT, None)

    @staticmethod
    def create_from_text(session_id: str, text: str):
        return Message(session_id, MessageType.MESSAGE, text.encode())

    @staticmethod
    def create_from_byte(session_id: str, array: bytes):
        return Message(session_id, MessageType.MESSAGE, array)

    @staticmethod
    def create_from_object(session_id: str, object_data: Any):
        return Message(session_id, MessageType.MESSAGE, json.dumps(object_data).encode("utf-8"))

    @staticmethod
    def create(session_id: str, data: Any):
        ret_val: Message = None
        if isinstance(data, str):
            ret_val = Message.create_from_text(
                session_id,  data)
        elif isinstance(data, bytes):
            ret_val = Message.create_from_byte(
                session_id,  data)
        else:
            ret_val = Message.create_from_object(
                session_id,  data)
        return ret_val

    @staticmethod
    def read(connection: socket.socket):
        message: Message = None
        data = connection.recv(1)
        if data:
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            data = connection.recv(4)
            data_len = int.from_bytes(data, byteorder='big', signed=True)
            data = connection.recv(data_len)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type != MessageType.NOT_EXIST:
                data = connection.recv(4)
                data_len = int.from_bytes(data, byteorder='big', signed=True)
                data = connection.recv(data_len)
                parameter = data
            message = Message(session_id, message_type, parameter)
        return message
