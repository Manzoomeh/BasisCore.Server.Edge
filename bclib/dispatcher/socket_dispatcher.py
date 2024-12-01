import asyncio
from dependency_injector import containers

from bclib.cache import CacheManager
from bclib.db_manager import DbManager
from bclib.logger import ILogger
from bclib.utility import DictEx
from bclib.listener import Endpoint, Message, SocketListener
from .routing_dispatcher import RoutingDispatcher


class SocketDispatcher(RoutingDispatcher):
    def __init__(self, container:'containers.Container', options: 'DictEx',cache_manager:'CacheManager',db_manager:'DbManager',logger:'ILogger',loop:'asyncio.AbstractEventLoop'=None):
        super().__init__(container= container, options=options,cache_manager=cache_manager,db_manager=db_manager,logger=logger,loop=loop)
        self.__lock = asyncio.Lock()
        self.__listener = SocketListener(
            Endpoint(self.options.receiver),
            Endpoint(self.options.sender),
            self._on_message_receive_async)

    async def send_message_async(self, message: Message) -> bool:
        """Send message to endpoint"""

        async with self.__lock:
            return await self.__listener.send_message_async(message)

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
