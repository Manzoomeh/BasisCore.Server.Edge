import asyncio
from ..named_pipe.windows_named_pipe_connection import WindowsNamedPipeConnection
from ..named_pipe.inamed_pipe_connection import INamedPipeConnection


class NamedPipeConnection:
    __dic: 'dict[str,INamedPipeConnection]' = dict()

    @staticmethod
    def get_connection(pipe_name: str, loop: asyncio.AbstractEventLoop) -> INamedPipeConnection:
        ret_val = None
        if pipe_name in NamedPipeConnection.__dic:
            ret_val = NamedPipeConnection.__dic[pipe_name]
        else:
            ret_val = NamedPipeConnection.__dic[pipe_name] = WindowsNamedPipeConnection(
                pipe_name, loop)
        return ret_val
