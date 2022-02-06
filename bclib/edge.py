import json
from pathlib import Path
import multiprocessing

from bclib.dispatcher import Dispatcher, IDispatcher, SocketDispatcher, DevServerDispatcher
from bclib.context import Context, WebContext, SocketContext, ClientSourceContext, ClientSourceMemberContext, RabbitContext, RESTfulContext, RequestContext, MergeType, ServerSourceContext, ServerSourceMemberContext, SourceContext, SourceMemberContext
from bclib.utility import DictEx, HttpStatusCodes, HttpMimeTypes, ResponseTypes, HttpHeaders
from bclib.listener import Message, MessageType, HttpBaseDataType, HttpBaseDataName
from bclib.predicate import Predicate
from bclib.exception import ShortCircuitErr, UnauthorizedErr, HandlerNotFoundErr, InternalServerErr, NotFoundErr
from bclib import __version__


def from_config(option_file_path: str, file_name: str = "host.json"):
    __print_splash(True)
    with open(Path(option_file_path).with_name(file_name), encoding="utf-8") as options_file:
        host_config = json.load(options_file)
    process_list: 'list[multiprocessing.Process]' = list()
    for options in host_config:
        options["__edge_multi_mode__"] = True
        code_file_path = options["code"]
        process = multiprocessing.Process(target=__run_edge_server, args=(
            code_file_path, Path(code_file_path).name, options))
        process_list.append(process)

    for process in process_list:
        process.start()

    for process in process_list:
        process.join()


def __run_edge_server(file_path: str, file_name: str, options: dict()):
    with open(file_path, encoding="utf-8") as file:
        code_str = file.read()
    code = compile(code_str, file_name, 'exec')
    exec(code, {"options": options})


def from_options(options: dict) -> Dispatcher:
    if "__edge_multi_mode__" not in options:
        __print_splash(False)
    ret_val: Dispatcher = None
    if "server" in options:
        ret_val = DevServerDispatcher(options)
    else:
        ret_val = SocketDispatcher(options)
    return ret_val


def __print_splash(inMultiMode: bool):
    print(f'''
______           _                          _____    _            
| ___ \         (_)                        |  ___|  | |           
| |_/ / __ _ ___ _ ___  ___ ___  _ __ ___  | |__  __| | __ _  ___ 
| ___ \/ _` / __| / __|/ __/ _ \| '__/ _ \ |  __|/ _` |/ _` |/ _ \\
| |_/ / (_| \__ \ \__ \ (_| (_) | | |  __/ | |__| (_| | (_| |  __/
\____/ \__,_|___/_|___/\___\___/|_|  \___| \____/\__,_|\__, |\___|
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
