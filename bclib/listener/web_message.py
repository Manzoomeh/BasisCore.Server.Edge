import json
from typing import Any, Coroutine, Optional, Union

from aiohttp import web
from aiohttp.web_response import ContentCoding

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType


class WebMessage(Message):
    """Message specialization for HTTP (dev server) flow.

    Holds the parsed cms_object directly to avoid JSON serialize/deserialize
    overhead when running inside the in-process development edge server.
    """

    def __init__(self, session_id: str, message_type: MessageType, cms_object: dict, request: 'web.Request' = None):
        # We deliberately do NOT serialize cms_object into buffer.
        super().__init__(session_id, message_type, buffer=None)
        self.cms_object = cms_object  # keep local
        self.__request = request
        self.Response = None

    def create_response_message(self, session_id: str, cms_object: dict) -> "Message":
        self.cms_object = cms_object  # update local cms_object
        ret_val = WebMessage(session_id, MessageType.AD_HOC,
                             cms_object, self.__request)
        ret_val.Response = self.Response
        return ret_val

    async def start_stream_response_async(self, status: int = 200,
                                          reason: Optional[str] = 'OK',
                                          headers: Optional[dict] = None) -> None:
        """Start streaming response for chunked data transfer"""
        if self.Response is not None:
            raise Exception('StreamResponse already started')
        if self.__request is None:
            raise Exception('Request not available for streaming')
        self.Response = web.StreamResponse(status=status,
                                           reason=reason,
                                           headers=headers)
        await self.Response.prepare(self.__request)

    async def write_async(self, data: bytes) -> Coroutine[Any, Any, None]:
        """Write data chunk to streaming response"""
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.write(data)

    async def drain_async(self) -> Coroutine[Any, Any, None]:
        """Drain the write buffer"""
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.drain()

    async def enable_compression(self, force: Optional[Union[bool, ContentCoding]] = None) -> None:
        """Enable compression for streaming response"""
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.enable_compression(force)
