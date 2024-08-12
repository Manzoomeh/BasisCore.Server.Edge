from typing import Any, TYPE_CHECKING, Coroutine, Optional, Union
from aiohttp.web_response import ContentCoding

from bclib.utility import HttpMimeTypes
from ..context.request_context import RequestContext

if TYPE_CHECKING:
    from .. import dispatcher
    from .. import listener


class WebContext(RequestContext):
    def __init__(self, cms_object: dict,  dispatcher: 'dispatcher.IDispatcher',message_object: 'listener.WebMessage') -> None:
        super().__init__(cms_object, dispatcher)
        self.process_async = True
        self.__message = message_object
    
    async def start_stream_response_async(self,status: int = 200,
        reason: Optional[str] = 'OK',
        headers: Optional[dict] = None,)-> Coroutine[Any, Any, None]:
        await self.__message.start_stream_response_async(status,reason,headers)

    async def write_async(self,data:'bytes') -> Coroutine[Any, Any, None]:
        await  self.__message.write_async(data)

    async def drain_async(self) -> Coroutine[Any, Any, None]:
        await self.__message.drain_async()
    
    async def write_and_drain_async(self,data:'bytes') -> Coroutine[Any, Any, None]:
        await self.write_async(data)
        await self.drain_async()

    async def enable_compression(self,force: Optional[Union[bool, ContentCoding]] = None) ->  None:
        await self.__message.enable_compression(force)
