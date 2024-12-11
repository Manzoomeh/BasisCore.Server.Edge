"""Main module of bclib.wrapper for all exist module that need in basic coding"""

import asyncio
from dependency_injector import providers
# from bclib.db_manager import *
# from bclib.dispatcher import RoutingDispatcher, IDispatcher, SocketDispatcher, DevServerDispatcher, EndpointDispatcher
# from bclib.context import Context, WebContext, SocketContext, ClientSourceContext, ClientSourceMemberContext, RabbitContext, RESTfulContext, RequestContext, MergeType, ServerSourceContext, ServerSourceMemberContext, SourceContext, SourceMemberContext, EndPointContext
from bclib.utility import DictEx, HttpStatusCodes, HttpMimeTypes, ResponseTypes, HttpHeaders
# from bclib.listener import Message, MessageType, HttpBaseDataType, HttpBaseDataName
from bclib.predicate import Predicate
from bclib.exception import *
from bclib.edge_container import EdgeContainer

from bclib.db_manager import DbManager, SqlDb, SQLiteDb, MongoDb, RabbitConnection, RESTfulConnection

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType
from bclib.listener.http_listener.http_base_data_name import HttpBaseDataName
from bclib.listener.http_listener.http_base_data_type import HttpBaseDataType


from bclib.dispatcher.idispatcher import IDispatcher
from bclib.dispatcher.socket_dispatcher import SocketDispatcher
from bclib.dispatcher.dev_server_dispatcher import DevServerDispatcher
from bclib.dispatcher.routing_dispatcher import RoutingDispatcher
from bclib.dispatcher.endpoint_dispatcher import EndpointDispatcher

from bclib.context.client_source_context import ClientSourceContext
from bclib.context.client_source_member_context import ClientSourceMemberContext
from bclib.context.context import Context
from bclib.context.restful_context import RESTfulContext
from bclib.context.web_context import WebContext
from bclib.context.request_context import RequestContext
from bclib.context.rabbit_context import RabbitContext
from bclib.context.socket_context import SocketContext
from bclib.context.merge_type import MergeType
from bclib.context.server_source_context import ServerSourceContext
from bclib.context.server_source_member_context import ServerSourceMemberContext
from bclib.context.source_context import SourceContext
from bclib.context.source_member_context import SourceMemberContext
from bclib.context.end_point_context import EndPointContext


from bclib import __version__


def from_config(option_file_path: str, file_name: str = "host.json"):
    """Create related RoutingDispatcher obj from config file in related path"""
    import json
    from pathlib import Path

    with open(Path(option_file_path).with_name(file_name), encoding="utf-8") as options_file:
        options = json.load(options_file)
    from_options(options)


def from_list(hosts: 'dict[str,list[str]]'):
    """Create related RoutingDispatcher obj from path list object"""
    import subprocess
    import asyncio
    import concurrent.futures

    __print_splash(True)
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(hosts.items())) as executor:
        tasks: list[asyncio.Future] = []
        for host, args in hosts.items():
            args.append(f"-n {host}")
            args.append("-m")
            tasks.append(loop.run_in_executor(executor, subprocess.run, args))
            print(f'{host} start running from {args[1]}')
        try:
            loop.run_until_complete(asyncio.gather(*tasks))
        except KeyboardInterrupt:
            pass


def from_options(options: 'dict', loop: 'asyncio.AbstractEventLoop' = None) -> 'RoutingDispatcher':
    container = EdgeContainer()
    container.app_config.from_dict(options)
    if loop:
        container.app_config.loop.from_value(loop)
    return from_container(container)


def __get_arg_parts(container: 'EdgeContainer'):
    import sys
    import getopt

    argument_list = sys.argv[1:]
    # Options
    short_options = "mn:"
    # Long options
    long_options = ["Name =", "Multi"]
    is_multi = False
    try:
        arguments, _ = getopt.gnu_getopt(
            argument_list, short_options, long_options)
        for current_argument, current_value in arguments:
            if current_argument in ("-n", "--Name"):
                container.app_config.name.from_value(current_value.strip())
            elif current_argument in ("-m", "--Multi"):
                is_multi = True
        container.app_config.is_multi.from_value(is_multi)
    except getopt.error as err:
        print(str(err))


def from_container(container: 'EdgeContainer') -> 'RoutingDispatcher':
    """Create related RoutingDispatcher obj from config object"""

    if type(container) is not EdgeContainer:
        container.app_container.override(providers.Object(container))
    __get_arg_parts(container)
    if not container.app_config.is_multi():
        __print_splash(False)
    return container.dispatcher()


def __print_splash(in_multi_mode: bool):
    print(f'''
______           _                          _____    _
| ___ \\         (_)                        |  ___|  | |
| |_/ / __ _ ___ _ ___  ___ ___  _ __ ___  | |__  __| | __ _  ___
| ___ \\/ _` / __| / __|/ __/ _ \\| '__/ _ \\ |  __|/ _` |/ _` |/ _ \\
| |_/ / (_| \\__ \\ \\__ \\ (_| (_) | | |  __/ | |__| (_| | (_| |  __/
\\____/ \\__,_|___/_|___/\\___\\___/|_|  \\___| \\____/\\__,_|\\__, |\\___|
                                                        __/ |
                                                       |___/
***********************************
Basiscore Edge

Welcome To BasisCore Ecosystem
Follow us on https://BasisCore.com/
bclib Version : {__version__}
Run in {'multi' if in_multi_mode else 'single'} instance mode!
***********************************
(Press CTRL+C to quit)
''')
