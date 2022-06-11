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

        named_pipe_handle.write(
            message.type.value.to_bytes(1, 'big'))

        data = message.session_id.encode()
        data_length_bytes = len(data).to_bytes(4, 'big')
        named_pipe_handle.write(
            data_length_bytes)

        named_pipe_handle.write(named_pipe_handle, data)

        if message.type in (MessageType.AD_HOC, MessageType.MESSAGE):
            data_length_bytes = len(message.buffer).to_bytes(4, 'big')
            named_pipe_handle.write(
                data_length_bytes)

            named_pipe_handle.write(
                named_pipe_handle, message.buffer)

        named_pipe_handle.flush()


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
