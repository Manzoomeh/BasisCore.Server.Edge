import asyncio
import sys

from dependency_injector import containers,providers
from bclib.logger import LoggerFactory
from bclib.db_manager import DbManager
from bclib.cache import CacheFactory
from bclib.utility import DictEx
from bclib.dispatcher import SocketDispatcher, DevServerDispatcher, EndpointDispatcher

def get_mode(options:'DictEx'):
    if options.has("server"):
        ret_val = 'server'
    elif options.has("endpoint"):
        ret_val = 'endpoint'
    else:
        ret_val = 'socket'
    return ret_val    

def create_loop(options:'DictEx') -> asyncio.AbstractEventLoop:
    loop:asyncio.AbstractEventLoop = options.loop
    if loop is None and sys.platform == 'win32':
            # By default Windows can use only 64 sockets in asyncio loop. This is a limitation of underlying select() API call.
            # Use Windows version of proactor event loop using IOCP
            loop = asyncio.ProactorEventLoop()
    current_loop = asyncio.get_event_loop()
    if loop is not None and current_loop != loop:
        asyncio.set_event_loop(loop)
    return asyncio.get_event_loop()

class EdgeContainer(containers.DeclarativeContainer):
    app_config = providers.Configuration()
    app_container = providers.Object(providers.Self())
    app_options = providers.Singleton(  DictEx,app_config)
    app_mode = providers.Singleton( get_mode,app_options)
    app_cache_options =providers.Singleton(lambda x:x.cache,app_options) 
    app_event_loop = providers.Singleton(create_loop,app_options)
    app_cache_manager = providers.Singleton(CacheFactory.create,app_cache_options)
    app_db_manager = providers.Singleton(DbManager,app_options, app_event_loop)
    app_logger= providers.Singleton(LoggerFactory.create,app_options)
    app_server_dispatcher = providers.Singleton(DevServerDispatcher,app_container, app_options,app_cache_manager,app_db_manager,app_logger,app_event_loop)
    app_endpoint_dispatcher = providers.Singleton(EndpointDispatcher,app_container,app_options,app_cache_manager,app_db_manager,app_logger,app_event_loop)
    app_socket_dispatcher = providers.Singleton(SocketDispatcher,app_container,app_options,app_cache_manager,app_db_manager,app_logger,app_event_loop)

    dispatcher = providers.Selector(
        app_mode,
        server=app_server_dispatcher,
        endpoint = app_endpoint_dispatcher,
        socket = app_socket_dispatcher
    )