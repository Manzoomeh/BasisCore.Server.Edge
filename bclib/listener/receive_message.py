import asyncio
import json

from bclib.listener.message_type import MessageType
from .message import Message


class SocketMessage(Message):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def fill_async(self):
        data = await self.reader.readexactly(1)
        if data:
            self.type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            data = await self.reader.readexactly(4)
            data_len = int.from_bytes(data, byteorder='big', signed=True)
            data = await self.reader.readexactly(data_len)
            self.session_id = data.decode("utf-8")
            if self.type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                data = await self.reader.readexactly(4)
                data_len = int.from_bytes(
                    data, byteorder='big', signed=True)
                data = await self.reader.readexactly(data_len)
                self.buffer = data

    async def write_result_async(self, cms: dict,message_type:'MessageType'):
        try:
            self.writer.write(message_type.value.to_bytes(1, 'big'))
            data = self.session_id.encode()
            data_length_bytes = len(data).to_bytes(4, 'big')
            self.writer.write(data_length_bytes)
            self.writer.write(data)
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE):
                result_bytes = json.dumps(
                    cms, ensure_ascii=False).encode("utf-8")
                data_length_bytes = len(result_bytes).to_bytes(4, 'big')
                self.writer.write(data_length_bytes)
                self.writer.write(result_bytes)
            await self.writer.drain()
        except asyncio.CancelledError:
            pass

    async def set_result_async(self, cms: dict):
        await self.write_result_async(cms,self.type)

    async def read_next_message_async(self) -> 'SocketMessage':
        ret_val = SocketMessage(self.reader, self.writer)
        await ret_val.fill_async()
        return ret_val

# class EndPointMessage(StreamBaseMessage):
#     def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#         super().__init__(reader, writer)


# class SocketMessage(StreamBaseMessage):
#     def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#         super().__init__(reader, writer)


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
