import asyncio

from context.context_factory import ContextFactory
from dependency_injector import containers

from bclib.logger import ILogger
from bclib.cache import CacheManager
from bclib.db_manager import DbManager
from bclib.utility import DictEx
from bclib.listener import Endpoint,  HttpListener
from bclib.dispatcher.routing_dispatcher import RoutingDispatcher


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self,container:'containers.Container', context_factory:'ContextFactory', options: 'DictEx',cache_manager:'CacheManager',db_manager:'DbManager',logger:'ILogger',loop:'asyncio.AbstractEventLoop'=None):
        super().__init__(container=container,context_factory=context_factory, options=options,cache_manager=cache_manager,db_manager=db_manager,logger = logger, loop=loop)
        self.__listener = HttpListener(
            Endpoint(self.options.server),
            self._on_message_receive_async,
            self.options.ssl,
            self.options.configuration
            )

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
