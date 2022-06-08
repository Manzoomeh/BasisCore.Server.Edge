"""Main module of bclib.wrapper for all exist module that need in basic coding"""

from re import T
from bclib.dispatcher import RoutingDispatcher, IDispatcher, SocketDispatcher, DevServerDispatcher, NamedPipeDispatcher
from bclib.context import Context, WebContext, SocketContext, ClientSourceContext, ClientSourceMemberContext, RabbitContext, RESTfulContext, RequestContext, MergeType, ServerSourceContext, ServerSourceMemberContext, SourceContext, SourceMemberContext, NamedPipeContext
from bclib.utility import DictEx, HttpStatusCodes, HttpMimeTypes, ResponseTypes, HttpHeaders, NamedPipeHelper
from bclib.listener import Message, MessageType, HttpBaseDataType, HttpBaseDataName
from bclib.predicate import Predicate
from bclib.exception import ShortCircuitErr, UnauthorizedErr, HandlerNotFoundErr, InternalServerErr, NotFoundErr
from bclib import __version__


def from_config(option_file_path: str, file_name: str = "host.json"):
    """Create related RoutingDispatcher obj from config file in related path"""
    import json
    from pathlib import Path

    with open(Path(option_file_path).with_name(file_name), encoding="utf-8") as options_file:
        options = json.load(options_file)
    from_options(options)


def from_list_(hosts: 'dict[str,list[str]]'):
    """Create related RoutingDispatcher obj from path list object"""
    import subprocess
    import asyncio

    __print_splash(True)
    loop = asyncio.get_event_loop()
    for host, args in hosts.items():
        try:
            args.append(f"-n {host}")
            args.append("-m")
            loop.run_in_executor(None, subprocess.run, args)
            print(f'{host} start runing from {args[1]}')
        except Exception as ex:
            print(ex)


def from_list(hosts: 'dict[str,list[str]]'):
    """Create related RoutingDispatcher obj from path list object"""
    import asyncio

    async def run_host_async(host_name: str, args: 'list[str]') -> None:
        print(f'{host_name} start running from {args[1]}')
        # try:
        proc = await asyncio.create_subprocess_shell(" ".join(args))
        # except Exception as ex:
        #     print()
        stdout, stderr = await proc.communicate()
        print(f'[{host_name!r} exited with {proc.returncode}]')
        if stdout:
            print(f'[stdout]\n{stdout.decode()}')
        if stderr:
            print(f'[stderr]\n{stderr.decode()}')

    __print_splash(True)
    tasks = []
    for host_name, args in hosts.items():
        args.append(f"-n {host_name}")
        args.append("-m")
        task = run_host_async(host_name, args)
        tasks.append(task)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except Exception as ex:
        print('g', repr(ex))
    # finally:
    #     tasks = asyncio.all_tasks(loop=loop)
    #     for task in tasks:
    #         task.cancel()
    #     group = asyncio.gather(*tasks, return_exceptions=True)
    #     loop.run_until_complete(group)
    #     loop.close()


def from_options(options: dict) -> RoutingDispatcher:
    """Create related RoutingDispatcher obj from config object"""

    import sys
    import getopt

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
    ret_val: RoutingDispatcher = None
    if "server" in options:
        ret_val = DevServerDispatcher(options)
    elif "named_pipe" in options:
        ret_val = NamedPipeDispatcher(options)
    else:
        ret_val = SocketDispatcher(options)
    return ret_val


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
