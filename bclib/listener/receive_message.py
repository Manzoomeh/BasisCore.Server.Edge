import asyncio

from .message_type import MessageType
from .message import Message


class ReceiveMessage(Message):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,  sessionId: str, messageType: MessageType, buffer: bytes = None) -> None:
        super().__init__(sessionId, messageType, buffer)
        self.reader = reader
        self.writer = writer

    async def read_next_message_async(self) -> 'ReceiveMessage':
        return await ReceiveMessage.read_from_stream_async(self.reader, self.writer)

    @staticmethod
    async def read_from_stream_async(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> 'ReceiveMessage':
        message: ReceiveMessage = None
        data = await reader.readexactly(1)
        if data:
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            data = await reader.readexactly(4)
            data_len = int.from_bytes(data, byteorder='big', signed=True)
            data = await reader.readexactly(data_len)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                data = await reader.readexactly(4)
                data_len = int.from_bytes(
                    data, byteorder='big', signed=True)
                data = await reader.readexactly(data_len)
                parameter = data
            message = ReceiveMessage(
                reader, writer, session_id, message_type, parameter)
        return message
