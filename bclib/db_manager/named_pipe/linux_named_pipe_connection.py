import asyncio
from io import BufferedReader, BufferedWriter
import json
import uuid
from typing import Any
from ..named_pipe.inamed_pipe_connection import INamedPipeConnection

from bclib.utility import LinuxNamedPipeHelper


class LinuxNamedPipeConnection(INamedPipeConnection):
    def __init__(self, pipe_name: str, event_loop: asyncio.AbstractEventLoop) -> None:
        self.__event_loop = event_loop
        self.__reader_pipe_name = F"{pipe_name}-reader"
        self.__writer_pipe_name = F"{pipe_name}-writer"
        self.__reader_pipe_handle: BufferedWriter = None
        self.__writer_pipe_handle: BufferedReader = None
        self.__query_list: 'dict[str,asyncio.Future]' = dict()
        self.__propcess_tesk = self.__event_loop.create_task(
            self.__get_receive_message_Task())

    async def __get_receive_message_Task(self):
        while True:
            try:
                if self.__writer_pipe_handle is None:
                    self.__writer_pipe_handle = open(
                        self.__writer_pipe_name, 'rb')
                message = await LinuxNamedPipeHelper.read_from_named_pipe_async(self.__writer_pipe_handle, self.__event_loop)
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
                self.__reader_pipe_handle = open(self.__reader_pipe_name, "wb")
            session_id = str(uuid.uuid4())
            msg = Message.create_add_hock(
                session_id, json.dumps(command).encode("utf-8"))
            LinuxNamedPipeHelper.write_to_named_pipe(
                msg, self.__reader_pipe_handle)
        except:
            self.__reader_pipe_handle = None
            raise
        return session_id

    def try_send_command(self, command: Any) -> bool:
        return True if self.__try_send_command(command) else False

    async def try_send_query_async(self, query: 'Any') -> 'Any':
        ret_val = None
        session_id = self.__try_send_command(query)
        if session_id:
            future = self.__event_loop.create_future()
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
