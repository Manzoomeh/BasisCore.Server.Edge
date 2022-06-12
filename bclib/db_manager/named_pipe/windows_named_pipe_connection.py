import asyncio
import json
import uuid
from typing import Any
from ..named_pipe.inamed_pipe_connection import INamedPipeConnection

from bclib.utility import WindowsNamedPipeHelper


class WindowsNamedPipeConnection(INamedPipeConnection):
    def __init__(self, pipe_name: str, event_loop: asyncio.AbstractEventLoop) -> None:
        self.__event_loop = event_loop
        self.__reader_pipe_name = F"{pipe_name}/reader"
        self.__writer_pipe_name = F"{pipe_name}/writer"
        self.__reader_pipe_handle = None
        self.__writer_pipe_handle = None
        self.__query_list: 'dict[str,asyncio.Future]' = dict()
        self.__propcess_tesk = self.__event_loop.create_task(
            self.__get_receive_message_Task())

    def __connect_to_reader_named_pipe(self):
        import win32file
        import pywintypes
        try:
            self.__reader_pipe_handle = win32file.CreateFile(self.__reader_pipe_name, win32file.GENERIC_WRITE,
                                                             0, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, None)
        except pywintypes.error as e:  # pylint: disable=maybe-no-member
            if e.args[0] == 2:   # ERROR_FILE_NOT_FOUND
                print(f"No Named Pipe '{self.__reader_pipe_name}'. {repr(e)}")
            else:
                print(
                    f"Named Pipe '{self.__reader_pipe_name}' error code {e.args[0]}. {repr(e)}")
            raise

    def __connect_to_writer_pipe(self):
        import win32file
        import pywintypes
        try:
            self.__writer_pipe_handle = win32file.CreateFile(self.__writer_pipe_name, win32file.GENERIC_READ,
                                                             0, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_READONLY, None)

        except pywintypes.error as e:  # pylint: disable=maybe-no-member
            if e.args[0] == 2:   # ERROR_FILE_NOT_FOUND
                print(f"No Named Pipe '{self.__writer_pipe_name}'. {repr(e)}")
            else:
                print(
                    f"Named Pipe '{self.__writer_pipe_name}' error code {e.args[0]}. {repr(e)}")
            raise

    async def __get_receive_message_Task(self):
        while True:
            try:
                if self.__writer_pipe_handle is None:
                    self.__connect_to_writer_pipe()
                message = await WindowsNamedPipeHelper.read_from_named_pipe_async(self.__writer_pipe_handle, self.__event_loop)
                if message and message.session_id in self.__query_list:
                    future = self.__query_list[message.session_id]
                    del self.__query_list[message.session_id]
                    data = json.loads(message.buffer)
                    future.get_loop().call_soon_threadsafe(future.set_result, data)
            except asyncio.CancelledError:
                self.clear_query_list()
                break
            except:
                self.__writer_pipe_handle = None
                self.clear_query_list()
                await asyncio.sleep(1)

    def __try_send_command(self, command: Any) -> str:
        from bclib.listener import Message
        session_id = None
        try:
            if self.__reader_pipe_handle is None:
                self.__connect_to_reader_named_pipe()
            session_id = str(uuid.uuid4())
            msg = Message.create_add_hock(
                session_id, json.dumps(command).encode("utf-8"))
            WindowsNamedPipeHelper.write_to_named_pipe(
                msg, self.__reader_pipe_handle)
        except:
            self.__reader_pipe_handle = None
        return session_id

    def try_send_command(self, command: Any) -> bool:
        return True if self.__try_send_command(command) else False

    async def try_send_query_async(self, query: 'Any') -> 'Any':
        ret_val = None
        session_id = self.__try_send_command(query)
        if session_id:
            future = asyncio.Future()
            self.__query_list[session_id] = future
            ret_val = await future
        return ret_val

    def clear_query_list(self):
        for session_id in self.__query_list:
            try:
                future = self.__query_list[session_id]
                future.get_loop().call_soon_threadsafe(
                    future.set_exception, Exception("Named Pipe is broken"))
            except:
                pass
        self.__query_list.clear()
