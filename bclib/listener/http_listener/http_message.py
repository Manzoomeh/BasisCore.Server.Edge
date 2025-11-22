import json
from typing import Any, Coroutine, Optional, Union

from aiohttp import web
from aiohttp.web_response import ContentCoding

from bclib.listener.icms_base_message import ICmsBaseMessage
from bclib.listener.iresponse_base_message import IResponseBaseMessage
from bclib.listener.message import Message


class HttpMessage(Message, ICmsBaseMessage, IResponseBaseMessage):
    """Message specialization for HTTP (dev server) flow.

    Holds the parsed cms_object directly to avoid JSON serialize/deserialize
    overhead when running inside the in-process development edge server.

    The response is set asynchronously via set_response_async() which updates
    the internal response_data that will be returned to the client.

    Example:
        ```python
        # Create HTTP message from request
        cms_object = await parse_request(request)
        message = HttpMessage(cms_object, request)

        # Dispatcher processes and sets response
        await dispatcher.on_message_receive_async(message)

        # Response is now available in message.response_data
        return web.json_response(message.response_data)
        ```
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

    async def set_response_async(self, cms_object: dict) -> None:
        """Set response data asynchronously

        Stores the response data that will be returned to the HTTP client.
        Called by the dispatcher after processing the request.

        Args:
            cms_object: The CMS object containing response data
        """
        self.response_data = cms_object

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
