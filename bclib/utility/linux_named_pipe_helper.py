import asyncio
from io import BufferedReader, BufferedWriter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.listener.message import Message


class LinuxNamedPipeHelper:

    @staticmethod
    def __read_from_named_pipe(named_pipe_handle: BufferedReader, future: asyncio.Future) -> None:
        from bclib.listener import Message, MessageType

        try:
            data = named_pipe_handle.read(1)
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            data = named_pipe_handle.read(4)
            data_len = int.from_bytes(
                data, byteorder='big', signed=True)
            data = named_pipe_handle.read(data_len)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                data = named_pipe_handle.read(4)
                data_len = int.from_bytes(
                    data, byteorder='big', signed=True)
                parameter = named_pipe_handle.read(
                    data_len)

        except Exception as ex:
            future.get_loop().call_soon_threadsafe(future.set_exception, ex)
        else:
            message = Message(session_id, message_type, parameter)
            future.get_loop().call_soon_threadsafe(future.set_result, message)

    @staticmethod
    async def read_from_named_pipe_async(named_pipe_handle: BufferedReader, loop: asyncio.AbstractEventLoop = None) -> 'Message':
        if not loop:
            loop = asyncio.get_event_loop()
        future = asyncio.Future()
        loop.run_in_executor(
            None, LinuxNamedPipeHelper.__read_from_named_pipe, named_pipe_handle, future)
        return await future

    @staticmethod
    def write_to_named_pipe(message: 'Message', named_pipe_handle: BufferedWriter):
        from bclib.listener import MessageType

        named_pipe_handle.write(message.type.value.to_bytes(1, 'big'))

        data = message.session_id.encode()
        data_length_bytes = len(data).to_bytes(4, 'big')
        named_pipe_handle.write(data_length_bytes)
        named_pipe_handle.write(data)

        if message.type in (MessageType.AD_HOC, MessageType.MESSAGE):
            data_length_bytes = len(message.buffer).to_bytes(4, 'big')
            named_pipe_handle.write(data_length_bytes)
            named_pipe_handle.write(message.buffer)

        named_pipe_handle.flush()
