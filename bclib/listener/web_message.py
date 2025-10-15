from typing import Any, Optional, Union, Coroutine
from aiohttp import web
from aiohttp.web_response import ContentCoding

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType


class WebMessage(Message):
    """Message specialization for HTTP (dev server) flow.

    Holds the parsed cms_object directly to avoid JSON serialize/deserialize
    overhead when running inside the in-process development edge server.
    """
    def __init__(self, request: 'web.Request', session_id: str, message_type: MessageType, cms_object: dict):
        # We deliberately do NOT serialize cms_object into buffer.
        super().__init__(session_id, message_type, buffer=None)
        self.__request = request
        self.cms_object = cms_object  # already a dict: {"cms": ...}
        self.Response: Optional[web.StreamResponse] = None

    def create_response_message(self, session_id: str, buffer: bytes) -> "Message":
        # For uniformity with existing dispatcher path. Buffer (JSON payload) may
        # still be produced by dispatcher logic. We keep cms_object unchanged.
        ret_val = WebMessage(self.__request, session_id, MessageType.AD_HOC, self.cms_object)
        ret_val.Response = self.Response
        # Provide buffer for any downstream code expecting it (e.g., logging)
        ret_val.buffer = buffer
        return ret_val

    async def start_stream_response_async(self, status: int = 200,
                                          reason: Optional[str] = 'OK',
                                          headers: Optional[dict] = None) -> None:
        if self.Response is not None:
            raise Exception('StreamResponse started')
        self.Response = web.StreamResponse(status=status, reason=reason, headers=headers)
        await self.Response.prepare(self.__request)

    async def write_async(self, data: bytes) -> Coroutine[Any, Any, None]:
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
