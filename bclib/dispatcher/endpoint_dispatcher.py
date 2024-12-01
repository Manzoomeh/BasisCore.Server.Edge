import asyncio

from dependency_injector import containers
from bclib.cache import CacheManager
from bclib.db_manager import DbManager
from bclib.logger import ILogger

from bclib.utility import DictEx
from bclib.listener import Endpoint, ReceiveMessage
from .routing_dispatcher import RoutingDispatcher


class EndpointDispatcher(RoutingDispatcher):
    def __init__(self, container:'containers.Container', options: 'DictEx',cache_manager:'CacheManager',db_manager:'DbManager',logger:'ILogger',loop:'asyncio.AbstractEventLoop'=None):
        super().__init__(container= container, options=options,cache_manager=cache_manager,db_manager=db_manager,logger=logger,loop=loop)
        self.__endpoint = Endpoint(self.options.endpoint)

    def initialize_task(self):
        super().initialize_task()

        async def on_connection_open(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            try:
                msg = await ReceiveMessage.read_from_stream_async(reader, writer)
                result = await self._on_message_receive_async(msg)
                await result.write_to_stream_async(writer)
            except:
                pass
            try:
                if writer.can_write_eof():
                    writer.write_eof()
                await writer.drain()
                writer.close()
            except:
                pass

        async def start_servers_async():
            server = await asyncio.start_server(on_connection_open, self.__endpoint.url, self.__endpoint.port,)
            print(
                f'Server up in {self.__endpoint.url}:{self.__endpoint.port} and wait for client connection...')
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            print("Server shutdown...")
            server.close()

        self.event_loop.create_task(start_servers_async())
