import asyncio
from io import BufferedWriter
import os
import sys
from typing import Callable, Coroutine
from ..listener.message import Message
from bclib.utility import LinuxNamedPipeHelper


class LinuxNamedPipeListener:
    """"""

    def __init__(self, pipe_name: str, on_message_receive_call_back: 'Callable[[Message], Coroutine[Message]]'):
        self.pipe_name = pipe_name
        self.__writer_pipe_name = F"{self.pipe_name}-writer"
        self.on_message_receive = on_message_receive_call_back
        self.__writer_pipe: BufferedWriter = None
        self.__event_loop: asyncio.AbstractEventLoop = None

    def try_unlink(self, pipe_name: str):
        try:
            os.unlink(pipe_name)
            print(f"unlink named pipe '{pipe_name}'...")
        except:
            pass

    async def __connect_writer_pipe_async(self):
        if self.__writer_pipe:
            self.try_unlink(self.__writer_pipe_name)

        try:
            os.mkfifo(self.__writer_pipe_name)
        except Exception as ex:
            print('error in run os.mkfifo():', ex)

        try:
            self.__writer_pipe = open(self.__writer_pipe_name, "wb")
            print(
                f"Writer named pipe '{self.__writer_pipe_name}' is created...")
        except Exception as ex:
            print(f"Error in create writer named pipe. {repr(ex)}")
            self.try_unlink(self.__writer_pipe_name)
            raise

    async def send_message_async(self, message: Message) -> bool:
        try_count = 0
        send = False
        while not send:
            try:
                if self.__writer_pipe is None:
                    await self.__connect_writer_pipe_async()
                LinuxNamedPipeHelper.write_to_named_pipe(
                    message, self.__writer_pipe)
                send = True
            except asyncio.CancelledError:
                break
            except Exception as ex:
                try_count = try_count+1
                if self.__writer_pipe:
                    self.try_unlink(self.__writer_pipe_name)
                    try:
                        self.__writer_pipe.close()
                    except:
                        pass
                    self.__writer_pipe = None
                print(f"Error in send message {ex}")
                if try_count > 3:
                    break
                await asyncio.sleep(.5)
        return send

    def initialize_task(self, loop: asyncio.AbstractEventLoop):
        self.__event_loop = loop

        async def reader_loop_async():
            reader_pipe_name = F"{self.pipe_name}-reader"
            while True:
                try:
                    os.mkfifo(reader_pipe_name)
                except Exception as ex:
                    print(
                        f'Error in call os.mkfifo() for ${reader_pipe_name}', ex)

                with open(reader_pipe_name, "rb") as reader_pipe:
                    print(
                        f"Reader named pipe '{reader_pipe_name}' is created. try to read from it...")
                    try:
                        while True:
                            message = await LinuxNamedPipeHelper.read_from_named_pipe_async(reader_pipe, self.__event_loop)
                            if message:
                                self.__event_loop.create_task(
                                    self.on_message_receive(message))
                    except asyncio.CancelledError:
                        print('Edge named pipe server stopped.!')
                        break
                    except Exception as ex:
                        print('Error cause edge named pipe server restart!', ex)
                        await asyncio.sleep(1)
                    finally:
                        try:
                            if reader_pipe:
                                os.unlink(reader_pipe_name)
                                print("unlink...")
                        except Exception as ex:
                            print("Error in unlink named pipe...", ex)

        self.__event_loop.create_task(reader_loop_async())
        self.__event_loop.create_task(self.__connect_writer_pipe_async())
