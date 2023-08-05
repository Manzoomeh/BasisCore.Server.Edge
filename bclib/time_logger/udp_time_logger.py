from bclib.utility import DictEx
from .base_time_logger import BaseTimeLogger
import typing
if typing.TYPE_CHECKING:
    from ..dispatcher.callback_info import CallbackInfo
    from bclib.context import Context

class UDPTimeLogger(BaseTimeLogger):
    def __init__(self, options: "DictEx") -> None:
        super().__init__(options)
        if "connections" not in options:
            raise KeyError("connections not found in time logger options!")
        self.__connections = options.connections
        if isinstance(self.__connections, dict):
            self.__connections = [self.__connections]
        for connection in self.__connections:
            if "ip" not in connection:
                raise KeyError("ip not found in connection!")
            if "port" not in connection:
                raise KeyError("port not found in connection!")
        
    def _log(self, execution_time: "int", handler: "CallbackInfo", context: "Context"):
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = f"FUNCTION {handler.callback_name} EXECUTED IN {execution_time:4d} MILLI SECONDS!"
        for connection in self.__connections:
            ip = connection["ip"]
            port = connection["port"]
            try:
                sock.sendto(bytes(message, encoding="utf-8"), (ip, port))
            except Exception as ex:
                print("Error in send timer log!", repr(ex), sep="\n")

    
