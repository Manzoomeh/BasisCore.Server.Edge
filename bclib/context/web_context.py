from itertools import islice
import json
from typing import Any, TYPE_CHECKING, Coroutine, Iterator, Optional, Union
from aiohttp.web_response import ContentCoding

from .request_context import RequestContext

if TYPE_CHECKING:
    from bclib.listener import WebMessage


class WebContext(RequestContext):
    def __init__(self, cms_object: dict,  dispatcher: 'IDispatcher',message_object: 'WebMessage') -> None:
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

    async def drain_array_async(self,data_list:Iterator,source_name:str, chunk_size:int,delimiter:str=',')-> Coroutine[Any, Any, None]:
        total_len =len(data_list)
        current:int = 0
        while current < total_len:
            temp_list = list(islice(data_list,current,current + chunk_size))
            current+= len(temp_list)
            data = {
                "sources": [
                {
                    "options": {
                    "tableName": source_name,
                    "mergeType": 1 #MergeType append,
                    },
                    "data": temp_list
                }],
            }
            await self.write_and_drain_async(f"{json.dumps(data)}{delimiter}".encode())
