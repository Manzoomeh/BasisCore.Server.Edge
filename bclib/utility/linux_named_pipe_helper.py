import asyncio
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.listener.message import Message


class LinuxNamedPipeHelper:

    @staticmethod
    def __check_read_error(error_code):
        if error_code != 0:
            raise Exception(
                f"error in read from pip. error code = {error_code}")

    @staticmethod
    def __check_write_error(error_code):
        if error_code != 0:
            raise Exception(
                f"error in write in pip. error code = {error_code}")

    @staticmethod
    def __read_from_named_pipe(named_pipe_handle: Any, future: asyncio.Future) -> None:
        import win32file
        from bclib.listener import Message, MessageType

        try:
            error, data = win32file.ReadFile(named_pipe_handle, 1)
            LinuxNamedPipeHelper.__check_read_error(error)
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            error, data = win32file.ReadFile(named_pipe_handle, 4)
            LinuxNamedPipeHelper.__check_read_error(error)
            data_len = int.from_bytes(
                data, byteorder='big', signed=True)
            error, data = win32file.ReadFile(named_pipe_handle, data_len)
            LinuxNamedPipeHelper.__check_read_error(error)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                error, data = win32file.ReadFile(named_pipe_handle, 4)
                LinuxNamedPipeHelper.__check_read_error(error)
                data_len = int.from_bytes(
                    data, byteorder='big', signed=True)
                error, parameter = win32file.ReadFile(
                    named_pipe_handle, data_len)
                LinuxNamedPipeHelper.__check_read_error(error)
        except Exception as ex:
            future.get_loop().call_soon_threadsafe(future.set_exception, ex)
        else:
            message = Message(session_id, message_type, parameter)
            future.get_loop().call_soon_threadsafe(future.set_result, message)

    @staticmethod
    async def read_from_named_pipe_async(named_pipe_handle: Any, loop: asyncio.AbstractEventLoop = None) -> 'Message':
        if not loop:
            loop = asyncio.get_event_loop()
        future = asyncio.Future()
        loop.run_in_executor(
            None, LinuxNamedPipeHelper.__read_from_named_pipe, named_pipe_handle, future)
        return await future

    @staticmethod
    def write_to_named_pipe(message: 'Message', named_pipe_handle: Any):
        import win32file
        import win32pipe
        import pywintypes
        from bclib.listener import MessageType

        try:
            error, _ = win32file.WriteFile(
                named_pipe_handle, message.type.value.to_bytes(1, 'big'))
            LinuxNamedPipeHelper.__check_write_error(error)
            data = message.session_id.encode()
            data_length_bytes = len(data).to_bytes(4, 'big')
            error, _ = win32file.WriteFile(
                named_pipe_handle, data_length_bytes)
            LinuxNamedPipeHelper.__check_write_error(error)
            error, _ = win32file.WriteFile(named_pipe_handle, data)
            LinuxNamedPipeHelper.__check_write_error(error)
            if message.type in (MessageType.AD_HOC, MessageType.MESSAGE):
                data_length_bytes = len(message.buffer).to_bytes(4, 'big')
                error, _ = win32file.WriteFile(
                    named_pipe_handle, data_length_bytes)
                LinuxNamedPipeHelper.__check_write_error(error)
                error, _ = win32file.WriteFile(
                    named_pipe_handle, message.buffer)
                LinuxNamedPipeHelper.__check_write_error(error)
            win32file.FlushFileBuffers(named_pipe_handle)
        except pywintypes.error as e:  # pylint: disable=maybe-no-member
            # Disconnect the named pipe
            win32pipe.DisconnectNamedPipe(named_pipe_handle)
            # CLose the named pipe
            win32file.CloseHandle(named_pipe_handle)
            if e.args[0] == 2:   # ERROR_FILE_NOT_FOUND
                print(f"No Named Pipe.  {repr(e)}")
            elif e.args[0] == 232:
                print(f"The Pipe is being closed. {repr(e)}")
            elif e.args[0] == 109:   # ERROR_BROKEN_PIPE
                print(f"Named Pipe is broken. {repr(e)}")
            else:
                print(f"Named Pipe error code {e.args[0]}. {repr(e)}")
            raise

    @staticmethod
    async def wait_for_client_connect_async(pipe_handler: any, loop: asyncio.AbstractEventLoop = None) -> None:
        import win32pipe
        future = asyncio.Future()

        def process(pipe_handler: any, future: asyncio.Future):
            try:
                win32pipe.ConnectNamedPipe(pipe_handler, None)
                future.set_result(True)
            except Exception as ex:
                future.set_exception(ex)
        if not loop:
            loop = asyncio.get_event_loop()
        loop.run_in_executor(None, process, pipe_handler, future)
        await future

# import asyncio
# import os

# import sys
# import time

# from aiofile import async_open

# path = "./my.fifo1"


# def send():
#     try:
#         try:
#             os.mkfifo(path)
#         except Exception as ex:
#             print('error in run mkfifo:', ex)

#         try:
#             fifo = open(path, "w")
#         except Exception as e:
#             print(e)
#             sys.exit()
#         x = 0
#         while x < 5:
#             fifo.write(str(x))
#             fifo.flush()
#             print("Sending:", str(x))
#             x += 1
#             time.sleep(2)
#         print("Closing")
#         fifo.close()
#     except Exception as ex:
#         print(ex)
#     finally:
#         try:
#             if fifo:
#                 os.unlink(path)
#                 print("unlink...")
#         except Exception as ex:
#             print("error in unlink...", ex)


# async def client():
#     await asyncio.sleep(1)
#     print("start")
#     try:
#         with async_open(path, "r") as fifo:
#             while True:
#                 r = await fifo.read(1)
#                 if len(r) == 0:
#                     print("no message")
#                     await asyncio.sleep(.5)
#                 else:
#                     print("Received:", len(r), r)
#         print("client terminate")
#     except Exception as e:
#         print(e)
#         sys.exit()


# # send()
# # client()
# loop = asyncio.get_event_loop()
# loop.run_in_executor(None, send)
# #t2 = loop.run_in_executor(None, client)
# loop.create_task(client())
# # loop.run_until_complete(t2)
# # asyncio.run(pipe_relay())
# loop.run_forever()
# print("end")
