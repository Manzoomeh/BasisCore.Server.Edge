import asyncio
from sys import platform
from ..named_pipe.inamed_pipe_connection import INamedPipeConnection


class NamedPipeConnection:
    __dic: 'dict[str,INamedPipeConnection]' = dict()

    @staticmethod
    def get_connection(pipe_name: str, loop: asyncio.AbstractEventLoop) -> INamedPipeConnection:
        ret_val = None
        if pipe_name in NamedPipeConnection.__dic:
            ret_val = NamedPipeConnection.__dic[pipe_name]
        else:
            # https://docs.python.org/3/library/sys.html#sys.platform
            if platform == "linux" or platform == "linux2":
                # linux
                from ..named_pipe.linux_named_pipe_connection import LinuxNamedPipeConnection
                ret_val = NamedPipeConnection.__dic[pipe_name] = LinuxNamedPipeConnection(
                    pipe_name, loop)
            elif platform == "darwin":
                # OS X
                raise Exception(
                    "named pipe connection not implemented in OS X")
            elif platform == "win32":
                from ..named_pipe.windows_named_pipe_connection import WindowsNamedPipeConnection
                ret_val = NamedPipeConnection.__dic[pipe_name] = WindowsNamedPipeConnection(
                    pipe_name, loop)
            NamedPipeConnection.__dic[pipe_name] = ret_val
        return ret_val
