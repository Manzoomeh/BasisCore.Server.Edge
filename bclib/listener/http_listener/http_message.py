import json
from typing import Any, Coroutine, Optional, Union

from aiohttp import web
from aiohttp.web_response import ContentCoding

from bclib.listener.cms_base_message import CmsBaseMessage


class HttpMessage(CmsBaseMessage):
    """Message specialization for HTTP (dev server) flow.

    Holds the parsed cms_object directly to avoid JSON serialize/deserialize
    overhead when running inside the in-process development edge server.
    """

    def __init__(self, cms_object: dict, request: 'web.Request' = None):
        # HttpMessage doesn't need session_id or type - uses cms_object and request
        self._cms_object = cms_object
        self.request = request
        self.Response = None
        self.response_data = None  # Store response data

    @property
    def cms_object(self) -> dict:
        """Get the CMS object for this message"""
        return self._cms_object

    def set_response(self, response_data: Any) -> None:
        """Set response data directly in this message"""
        self.response_data = response_data
        self._cms_object = response_data  # Update cms_object with response

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
