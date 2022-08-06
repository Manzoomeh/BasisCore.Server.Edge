import asyncio
from typing import Callable, Coroutine
from ..listener.message import Message
from bclib.utility import WindowsNamedPipeHelper


class WindowsNamedPipeListener:
    """"""

    def __init__(self, pipe_name: str, on_message_receive_call_back: 'Callable[[Message], Coroutine[Message]]'):
        self.pipe_name = pipe_name
        self.on_message_receive = on_message_receive_call_back
        self.__writer_pipe = None
        self.__reader_pipe = None
        self.__event_loop: asyncio.AbstractEventLoop = None

    async def __connect_writer_pipe_async(self):
        import win32pipe
        import pywintypes
        try:
            name = F"{self.pipe_name}/writer"
            self.__writer_pipe = win32pipe.CreateNamedPipe(name, win32pipe.PIPE_ACCESS_OUTBOUND,
                                                           win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                                           1, 65536, 65536, 0, None)
            print(
                f"Writer named pipe '{name}' is created. Waiting for reader client to connect...")
            await WindowsNamedPipeHelper.wait_for_client_connect_async(self.__writer_pipe, self.__event_loop)
            print(
                f"Reader client is connected to '{name}'...")
        except pywintypes.error as e:  # pylint: disable=maybe-no-member
            self.__writer_pipe = None
            if e.args[0] == 2:   # ERROR_FILE_NOT_FOUND
                print(f"No Named Pipe.  {repr(e)}")
            else:
                print(f"Named Pipe error code {e.args[0]}. {repr(e)}")
            raise
        except Exception as ex:
            self.__writer_pipe = None
            print(f"Error in create writer named pipe. {repr(ex)}")
            raise

    async def __process_message_async(self, message: 'Message') -> None:
        result = await self.on_message_receive(message)
        if result:
            await self.send_message_async(result)

    async def send_message_async(self, message: Message) -> bool:
        try_count = 0
        send = False
        while not send:
            try:
                if self.__writer_pipe is None:
                    await self.__connect_writer_pipe_async()
                WindowsNamedPipeHelper.write_to_named_pipe(
                    message, self.__writer_pipe)
                send = True
            except asyncio.CancelledError:
                break
            except Exception as ex:
                try_count = try_count+1
                self.__writer_pipe = None
                print(f"Error in send message {ex}")
                if try_count > 3:
                    break
                await asyncio.sleep(.5)
        return send

    def initialize_task(self, loop: asyncio.AbstractEventLoop):
        self.__event_loop = loop

        async def reader_loop_async():
            import win32pipe
            import win32file
            import pywintypes
            while True:
                try:
                    name = F"{self.pipe_name}/reader"
                    self.__reader_pipe = win32pipe.CreateNamedPipe(name, win32pipe.PIPE_ACCESS_INBOUND,
                                                                   win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                                                   1, 65536, 65536, 0, None)
                    print(
                        f"Reader named pipe '{name}' is created. Waiting for writer client to connect...")
                    await WindowsNamedPipeHelper.wait_for_client_connect_async(self.__reader_pipe, self.__event_loop)
                    print(
                        f"Writer client connect to '{name}'...")
                    while True:
                        message = await WindowsNamedPipeHelper.read_from_named_pipe_async(
                            self.__reader_pipe, self.__event_loop)
                        if message:
                            self.__event_loop.create_task(
                                self.__process_message_async(message))
                except asyncio.CancelledError:
                    print('Edge named pipe server stopped.!')
                    break
                except pywintypes.error as e:  # pylint: disable=maybe-no-member
                    if e.args[0] == 2:   # ERROR_FILE_NOT_FOUND
                        print(f"No reader named pipe.  {repr(e)}")
                    elif e.args[0] == 109:   # ERROR_BROKEN_PIPE
                        print(f"Reader named pipe is broken. {repr(e)}")
                    else:
                        print(
                            f"Reader named pipe error code {e.args[0]}. {repr(e)}")
                finally:
                    # Disconnect the named pipe
                    win32pipe.DisconnectNamedPipe(self.__reader_pipe)
                    # CLose the named pipe
                    win32file.CloseHandle(self.__reader_pipe)
        self.__event_loop.create_task(reader_loop_async())
        self.__event_loop.create_task(self.__connect_writer_pipe_async())
