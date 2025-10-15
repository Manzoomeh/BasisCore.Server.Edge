from typing import Any, Coroutine, Optional, Union

from aiohttp import web
from aiohttp.web_response import ContentCoding

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType


class SocketMessage(Message):
    def __init__(self,  request: 'web.Request', sessionId: str,  messageType: MessageType, buffer: bytes = None) -> None:
        super().__init__(sessionId, messageType, buffer)
        self.__request = request
        self.Response = None

    def create_response_message(self, session_id: str, buffer: bytes) -> "Message":
        ret_val = SocketMessage(
            self.__request, session_id, MessageType.AD_HOC, buffer)
        ret_val.Response = self.Response
        return ret_val

    async def start_stream_response_async(self, status: int = 200,
                                          reason: Optional[str] = 'OK',
                                          headers: Optional[dict] = None,):
        if self.Response is not None:
            raise Exception('StreamResponse started')
        self.Response = web.StreamResponse(status=status,
                                           reason=reason,
                                           headers=headers)
        await self.Response.prepare(self.__request)

    async def write_async(self, data: 'bytes') -> Coroutine[Any, Any, None]:
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.write(data)

    async def drain_async(self) -> Coroutine[Any, Any, None]:
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.drain()

    async def enable_compression(self, force: Optional[Union[bool, ContentCoding]] = None) -> None:
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.enable_compression(force)
