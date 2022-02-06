import asyncio
import json
from typing import Any


from ..listener.message_type import MessageType


class Message:
    def __init__(self, sessionId: str,  messageType: MessageType, buffer: bytes = None) -> None:
        self.session_id = sessionId
        self.type = messageType
        self.buffer = buffer

    async def write_to_stream_async(self, stream: asyncio.StreamWriter) -> bool:
        is_send = True
        try:
            stream.write(self.type.value.to_bytes(1, 'big'))
            data = self.session_id.encode()
            data_length_bytes = len(data).to_bytes(4, 'big')
            stream.write(data_length_bytes)
            stream.write(data)

            if self.type in (MessageType.AD_HOC, MessageType.MESSAGE):
                data_length_bytes = len(self.buffer).to_bytes(4, 'big')
                stream.write(data_length_bytes)
                stream.write(self.buffer)
            await stream.drain()
        except asyncio.CancelledError:
            is_send = False
        return is_send

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
    async def read_from_stream_async(stream: asyncio.StreamReader) -> 'Message':
        message: Message = None
        data = await stream.readexactly(1)
        if data:
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            data = await stream.readexactly(4)
            data_len = int.from_bytes(data, byteorder='big', signed=True)
            data = await stream.readexactly(data_len)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                data = await stream.readexactly(4)
                data_len = int.from_bytes(
                    data, byteorder='big', signed=True)
                data = await stream.readexactly(data_len)
                parameter = data
            message = Message(session_id, message_type, parameter)
        return message
