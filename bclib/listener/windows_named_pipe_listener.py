import asyncio
from typing import Callable, Coroutine
from ..listener.message import Message
from ..listener.message_type import MessageType


class WindowsNamedPipeListener:
    """"""

    def __init__(self, pipe_name: str, on_message_receive_call_back: 'Callable[[Message], Coroutine[Message]]'):
        self.pipe_name = pipe_name
        self.on_message_receive = on_message_receive_call_back
        self.__writer_pipe = None
        self.__reader_pipe = None

    async def __connect_writer_pipe_async(self):
        import win32pipe
        import pywintypes
        while True:
            try:
                name = F"{self.pipe_name}/writer"
                self.__writer_pipe = win32pipe.CreateNamedPipe(name, win32pipe.PIPE_ACCESS_OUTBOUND,
                                                               win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                                               1, 65536, 65536, 0, None)
                print(
                    f"Writer named pipe '{name}' is created. Waiting for reader client to connect..")
                win32pipe.ConnectNamedPipe(self.__writer_pipe, None)
                print(f"Reader client is connected to '{name}'.")
                break
            except pywintypes.error as e:
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

    async def send_message_async(self, message: Message) -> bool:
        try:
            if self.__writer_pipe is None:
                await self.__connect_writer_pipe_async()
            ret_val = self.__write_to_named_pipe(message, self.__writer_pipe)
        except Exception as ex:
            print(f"Error in send message {ex}")
            ret_val = False
        return ret_val

    def initialize_task(self, loop: asyncio.AbstractEventLoop):

        async def reader_loop_async():
            import win32pipe
            import win32file
            import pywintypes
            loop_ = asyncio.get_running_loop()
            while True:
                try:
                    name = F"{self.pipe_name}/reader"
                    self.__reader_pipe = win32pipe.CreateNamedPipe(name, win32pipe.PIPE_ACCESS_INBOUND,
                                                                   win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                                                   1, 65536, 65536, 0, None)
                    print(
                        f"Reader named pipe '{name}' is created. Waiting for writer client to connect.")
                    win32pipe.ConnectNamedPipe(self.__reader_pipe, None)
                    print("Writer client connect to reader named pipe.")
                    while True:
                        message = await self.read_message_async(
                            self.__reader_pipe)
                        if message:
                            loop_.create_task(self.on_message_receive(message))
                except asyncio.CancelledError:
                    print('closed by sender!')
                    break
                except pywintypes.error as e:
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
        loop.create_task(reader_loop_async())

    async def read_message_async(self, pyHandle: any) -> 'Message':
        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        loop.run_in_executor(
            None, self.__read_from_named_pipe_async, pyHandle, future)
        return await future

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
    def __read_from_named_pipe_async(pyHandle: any, future: asyncio.Future) -> None:
        import win32file

        try:
            error, data = win32file.ReadFile(pyHandle, 1)
            WindowsNamedPipeListener.__check_read_error(error)
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))
            error, data = win32file.ReadFile(pyHandle, 4)
            WindowsNamedPipeListener.__check_read_error(error)
            data_len = int.from_bytes(
                data, byteorder='big', signed=True)
            error, data = win32file.ReadFile(pyHandle, data_len)
            WindowsNamedPipeListener.__check_read_error(error)
            session_id = data.decode("utf-8")
            parameter = None
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                error, data = win32file.ReadFile(pyHandle, 4)
                WindowsNamedPipeListener.__check_read_error(error)
                data_len = int.from_bytes(
                    data, byteorder='big', signed=True)
                error, parameter = win32file.ReadFile(
                    pyHandle, data_len)
                WindowsNamedPipeListener.__check_read_error(error)
        except Exception as ex:
            future.get_loop().call_soon_threadsafe(future.set_exception, ex)
        else:
            message = Message(session_id, message_type, parameter)
            future.get_loop().call_soon_threadsafe(future.set_result, message)

    def __write_to_named_pipe(self, message: Message, pyHandle: any):
        import win32file
        import win32pipe
        import pywintypes

        try:
            is_send = False
            error, _ = win32file.WriteFile(
                pyHandle, message.type.value.to_bytes(1, 'big'))
            WindowsNamedPipeListener.__check_write_error(error)
            data = message.session_id.encode()
            data_length_bytes = len(data).to_bytes(4, 'big')
            error, _ = win32file.WriteFile(
                pyHandle, data_length_bytes)
            WindowsNamedPipeListener.__check_write_error(error)
            error, _ = win32file.WriteFile(pyHandle, data)
            WindowsNamedPipeListener.__check_write_error(error)

            if message.type in (MessageType.AD_HOC, MessageType.MESSAGE):
                data_length_bytes = len(message.buffer).to_bytes(4, 'big')
                error, _ = win32file.WriteFile(
                    pyHandle, data_length_bytes)
                WindowsNamedPipeListener.__check_write_error(error)
                error, _ = win32file.WriteFile(
                    pyHandle, message.buffer)
                WindowsNamedPipeListener.__check_write_error(error)
            win32file.FlushFileBuffers(pyHandle)
            is_send = True
        except pywintypes.error as e:
            # Disconnect the named pipe
            win32pipe.DisconnectNamedPipe(self.__writer_pipe)
            # CLose the named pipe
            win32file.CloseHandle(self.__writer_pipe)
            self.__writer_pipe = None
            if e.args[0] == 2:   # ERROR_FILE_NOT_FOUND
                print(f"No Named Pipe.  {repr(e)}")
            elif e.args[0] == 232:
                print(f"The Pipe is being closed. {repr(e)}")
            elif e.args[0] == 109:   # ERROR_BROKEN_PIPE
                print(f"Named Pipe is broken. {repr(e)}")
            else:
                print(f"Named Pipe error code {e.args[0]}. {repr(e)}")
        except:
            raise
        return is_send
