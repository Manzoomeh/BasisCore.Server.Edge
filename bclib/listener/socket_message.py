import asyncio
import json
from typing import Any, Coroutine, Optional

from bclib.listener.message_type import MessageType
from .message import Message


class SocketMessage(Message):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.buffer:Optional[bytes] = None

    async def get_json_async(self)-> Coroutine[Any, Any, dict]:
        await self.__fill_async()
        return json.loads(self.buffer)

    async def __fill_async(self) -> Coroutine[Any, Any, None]:
        if self.buffer is None:
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
        await ret_val.__fill_async()
        return ret_val