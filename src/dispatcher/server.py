import json
from pathlib import Path
import multiprocessing
import dispatcher


def from_config(file_path: str, file_name: str = "host.json"):
    with open(Path(file_path).with_name(file_name)) as options_file:
        host_config = json.load(options_file)
    process_list: list[multiprocessing.Process] = list()
    for options in host_config:
        file_path = options["code"]
        process = multiprocessing.Process(target=__run_edge_server, args=(
            file_path, Path(file_path).name, options))
        process_list.append(process)

    for process in process_list:
        process.start()

    for process in process_list:
        process.join()


def __run_edge_server(file_path: str, file_name: str, options: dict()):
    with open(file_path) as file:
        code_str = file.read()
    code = compile(code_str, file_name, 'exec')
    exec(code, {"options": options})


def from_options(options: dict) -> dispatcher.Dispatcher:
    ret_val: dispatcher.Dispatcher = None
    if "server" in options:
        ret_val = dispatcher.DevServerDispatcher(options)
    else:
        ret_val = dispatcher.SocketDispatcher(options)
    return ret_val
