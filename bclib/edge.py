"""Main module of bclib.wrapper for all exist module that need in basic coding"""

import asyncio

from bclib import __version__
from bclib.context import (ClientSourceContext, ClientSourceMemberContext,
                           Context, MergeType, RabbitContext, RequestContext,
                           RESTfulContext, ServerSourceContext,
                           ServerSourceMemberContext, SocketContext,
                           SourceContext, SourceMemberContext, WebContext,
                           WebSocketContext)
from bclib.db_manager import *
from bclib.dispatcher import Dispatcher, IDispatcher, WebSocketSession
from bclib.exception import *
from bclib.listener import (HttpBaseDataName, HttpBaseDataType, Message,
                            MessageType)
from bclib.predicate import Predicate
from bclib.utility import (DictEx, HttpHeaders, HttpMimeTypes, HttpStatusCodes,
                           ResponseTypes, StaticFileHandler)


def from_config(option_file_path: str, file_name: str = "host.json"):
    """Create related RoutingDispatcher obj from config file in related path"""
    import json
    from pathlib import Path

    with open(Path(option_file_path).with_name(file_name), encoding="utf-8") as options_file:
        options = json.load(options_file)
    from_options(options)


def from_list(hosts: 'dict[str,list[str]]'):
    """Create related RoutingDispatcher obj from path list object"""
    import concurrent.futures
    import subprocess

    __print_splash(True)
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(hosts.items())) as executor:
        tasks: list[asyncio.Future] = []
        for host, args in hosts.items():
            args.append(f"-n {host}")
            args.append("-m")
            tasks.append(loop.run_in_executor(executor, subprocess.run, args))
            print(f'{host} start running from {args[1]}')
        loop.run_until_complete(asyncio.gather(*tasks))


def from_options(options: dict, loop: asyncio.AbstractEventLoop = None) -> Dispatcher:
    """Create Dispatcher with appropriate listeners based on configuration"""
    import getopt
    import sys

    from bclib.listener import Endpoint, HttpListener, SocketListener

    multi: bool = False
    argumentList = sys.argv[1:]
    # Options
    short_options = "mn:"
    # Long options
    long_options = ["Name =", "Multi"]
    try:
        arguments, _ = getopt.gnu_getopt(
            argumentList, short_options, long_options)
        for current_argument, current_value in arguments:
            if current_argument in ("-n", "--Name"):
                options["name"] = current_value.strip()
            elif current_argument in ("-m", "--Multi"):
                multi = True
    except getopt.error as err:
        print(str(err))

    if not multi:
        __print_splash(False)

    # Create single Dispatcher instance
    dispatcher = Dispatcher(options=options, loop=loop)

    # Add appropriate listeners based on configuration
    if "server" in options:
        # HTTP/HTTPS server listener
        listener = HttpListener(
            Endpoint(dispatcher.options.server),
            dispatcher.on_message_receive_async,
            dispatcher.options.ssl if dispatcher.options.has("ssl") else None,
            dispatcher.options.configuration if dispatcher.options.has(
                "configuration") else None,
            dispatcher.ws_manager
        )
        dispatcher.add_listener(listener)

    if "receiver" in options and "sender" in options:
        # Socket listener (can coexist with HTTP server)
        listener = SocketListener(
            Endpoint(dispatcher.options.receiver),
            Endpoint(dispatcher.options.sender),
            dispatcher.on_message_receive_async
        )
        dispatcher.add_listener(listener)
        # Store listener reference for send_message_async
        dispatcher._socket_listener = listener

    if "endpoint" in options:
        # TCP endpoint listener
        async def on_connection_open(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            from bclib.listener import ReceiveMessage
            try:
                msg = await ReceiveMessage.read_from_stream_async(reader, writer)
                result = await dispatcher.on_message_receive_async(msg)
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

        # Store endpoint connection handler
        dispatcher._endpoint_connection_handler = on_connection_open
        dispatcher._endpoint = Endpoint(dispatcher.options.endpoint)

    return dispatcher


def __print_splash(inMultiMode: bool):
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
Run in {'multi' if inMultiMode else 'single'} instance mode!
***********************************
(Press CTRL+C to quit)
''')
