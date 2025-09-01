import asyncio
from typing import Callable, Coroutine

from ..listener.receive_message import ReceiveMessage
from ..listener.message import Message
from ..listener.endpoint import Endpoint


class SocketListener:
    def __init__(self, receiver: Endpoint, sender: Endpoint, on_message_receive_call_back: 'Callable[[Message], Coroutine[Message]]'):
        self.__receiver_endpoint = receiver
        self.__sender_endpoint = sender
        self.on_message_receive = on_message_receive_call_back
        self.__sender_stream_writer: asyncio.StreamWriter = None
        self.__receiver_server: asyncio.AbstractServer = None
        self.__sender_server: asyncio.AbstractServer = None

    async def __process_message_async(self, message: 'ReceiveMessage') -> None:
        result = await self.on_message_receive(message)
        if result:
            await self.send_message_async(result)

    async def send_message_async(self, message: Message) -> bool:
        try:
            await message.write_to_stream_async(self.__sender_stream_writer)
        except Exception as ex:
            print(f"Error in send message {ex}")
            return False

    async def on_sender_client_connect(self, _: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_name = writer.get_extra_info('peername')
        print(f'Reader from {peer_name}, connect to sender!')
        if self.__sender_stream_writer and not self.__sender_stream_writer.is_closing():
            if self.__sender_stream_writer.can_write_eof():
                self.__sender_stream_writer.write_eof()
                await self.__sender_stream_writer.drain()
            self.__sender_stream_writer.close()
            await self.__sender_stream_writer.wait_closed()
        self.__sender_stream_writer = writer
        cause = "closed!"
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            cause = 'closed by sender!'
        except (ConnectionResetError, asyncio.IncompleteReadError):
            cause = 'disconnected!'
        finally:
            print(
                f'Reader from {peer_name}, {cause}')
            if writer and not writer.is_closing():
                if writer.can_write_eof():
                    writer.write_eof()
                    await writer.drain()
                writer.close()
                await writer.wait_closed()

    async def on_receiver_client_connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_name = writer.get_extra_info('peername')
        print(f'Writer from {peer_name}, connect to receiver!')
        loop = asyncio.get_running_loop()
        cause = "closed!"
        try:
            while True:
                message: ReceiveMessage = await ReceiveMessage.read_from_stream_async(reader, writer)
                if message:
                    loop.create_task(self.__process_message_async(message))
        except asyncio.CancelledError:
            cause = 'closed by receiver!'
        except (ConnectionResetError, asyncio.IncompleteReadError):
            cause = 'disconnected!'
        finally:
            print(
                f'Writer from {peer_name}, {cause}')
            if writer and not writer.is_closing():
                if writer.can_write_eof():
                    writer.write_eof()
                    await writer.drain()
                writer.close()
                await writer.wait_closed()

    def initialize_task(self, loop: asyncio.AbstractEventLoop):
        async def start_servers_async():
            loop = asyncio.get_running_loop()
            try:
                self.__sender_server = await asyncio.start_server(
                    self.on_sender_client_connect,
                    host=self.__sender_endpoint.url,
                    port=self.__sender_endpoint.port)
                print(
                    f'Sender server up in {self.__sender_endpoint.url}:{self.__sender_endpoint.port} and wait for reader connection...')
                self.__receiver_server = await asyncio.start_server(
                    self.on_receiver_client_connect,
                    host=self.__receiver_endpoint.url,
                    port=self.__receiver_endpoint.port)
                print(
                    f'Receiver server up in {self.__receiver_endpoint.url}:{self.__receiver_endpoint.port} and wait for writer connection...')
            except Exception as ex:
                try:
                    if self.__sender_server:
                        self.__sender_server.close()
                        await self.__sender_server.wait_closed()
                except:
                    pass
                try:
                    if self.__receiver_server:
                        self.__receiver_server.close()
                        await self.__receiver_server.wait_closed()
                except:
                    pass
                print(f"server not start. {repr(ex)}")
                return

            async def sender_loop_async():
                try:
                    async with self.__sender_server:
                        await self.__sender_server.serve_forever()
                except asyncio.CancelledError:
                    self.__sender_server.close()
                    await self.__sender_server.wait_closed()
                    print("Sender server shutdown...")

            async def receiver_loop_async():
                try:
                    async with self.__receiver_server:
                        await self.__receiver_server.serve_forever()
                except asyncio.CancelledError:
                    self.__receiver_server.close()
                    await self.__receiver_server.wait_closed()
                    print("Receiver server shutdown...")
            loop.create_task(sender_loop_async())
            loop.create_task(receiver_loop_async())
        loop.create_task(start_servers_async())
