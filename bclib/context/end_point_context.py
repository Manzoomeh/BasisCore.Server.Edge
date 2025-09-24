from typing import Any
from bclib.dispatcher.idispatcher import IDispatcher
from bclib.listener.end_point_message import  EndPointMessage
from bclib.context.context import Context
from bclib.listener.message_type import MessageType
from bclib.utility import DictEx, HttpMimeTypes, HttpStatusCodes, ResponseTypes


import json


class EndPointContext(Context):
    """Base class for dispatching end point socket base request context"""

    def __init__(self, cms_object: 'dict',  dispatcher: 'IDispatcher', message_object: 'EndPointMessage', body: 'dict') -> None:
        super().__init__(dispatcher)
        self.cms = DictEx(cms_object) if cms_object else None
        self.url: str = self.cms.request.url if cms_object else None
        self.body = DictEx(body) if body else None
        self.message = message_object
        self.is_adhoc = False

    async def send_object_async(self, obj) -> None:
        await self.send_content_async(json.dumps(obj))

    async def send_html_async(self, html) -> None:
        await self.send_content_async(html, mime=HttpMimeTypes.HTML)

    async def send_code_async(self, code) -> None:
        await self.send_content_async(code, response_type=ResponseTypes.RENDERABLE, mime=HttpMimeTypes.HTML)

    async def send_content_async(self,
                                 content: 'Any',
                                 response_type: 'str' = ResponseTypes.RENDERED,
                                 status_code: 'str' = HttpStatusCodes.OK,
                                 mime: 'str' = HttpMimeTypes.JSON,
                                 template: 'DictEx' = None,
                                 headers: 'dict' = None) -> None:
        cms = Context._generate_response_cms(
            content, response_type, status_code, mime, template, headers)
        await self.message.write_result_async(cms,MessageType.MESSAGE)

    async def read_message_async(self) -> 'EndPointMessage':
        return await self.message.read_next_message_async()

    async def send_close_async(self) -> None:
        await self.message.write_result_async(None,MessageType.DISCONNECT)