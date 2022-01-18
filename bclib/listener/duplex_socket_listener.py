import asyncio
import socket
from struct import error
from typing import Any, Callable
from ..listener.message import Message
from ..listener.endpoint import EndPoint


class DuplexSocketListener:
    def __init__(self, receiver: EndPoint, sender: EndPoint, on_message_receive_call_back: 'Callable[[Message], Message]'):
        self.__receiver_endpoint = receiver
        self.__sender_endpoint = sender
        self.on_message_receive = on_message_receive_call_back
        self.__sender_socket = None

    def send_message(self, message: Message) -> bool:
        return message.write(self.__sender_socket)

    def __start_receiver(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receiver_socket:
                    receiver_socket.bind((self.__receiver_endpoint.url,
                                          self.__receiver_endpoint.port))
                    receiver_socket.listen()
                    print(
                        f'Receiver up in {self.__receiver_endpoint.url}:{self.__receiver_endpoint.port} and ready to connect')
                    connection, address = receiver_socket.accept()
                    loop.run_in_executor(
                        None, self.__on_receiver_connection_accepted, connection, address, loop)
            except error as ex:
                print(f'Error in connect receiver. {repr(ex)}')

    def __on_receiver_connection_accepted(self, socket_connection: socket.socket, address: Any, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        print(f'{address} connect to receiver')
        with socket_connection:
            while True:
                try:
                    message = Message.read(socket_connection)
                    if not message:
                        break
                except error as ex:
                    print(f"error in receiver {ex}")
                    break
                loop.run_in_executor(
                    None, self.on_message_receive, message)
        print(f'{address} disconnect from receiver')

    def __start_sender(self, _):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sender_socket:
                    sender_socket.bind((self.__sender_endpoint.url,
                                        self.__sender_endpoint.port))
                    sender_socket.listen()
                    print(
                        f'Sender is up in {self.__sender_endpoint.url}:{self.__sender_endpoint.port} and ready to connect')
                    self.__sender_socket, addr = sender_socket.accept()
                    print(f'{addr} connect to sender')

            except error as ex:
                print(f"error in sender {ex}")

    async def process_async(self):
        while True:
            loop = asyncio.get_event_loop()
            sender_task = loop.run_in_executor(
                None, self.__start_sender, loop)
            receiver_task = loop.run_in_executor(
                None, self.__start_receiver, loop)
            await asyncio.gather(receiver_task, sender_task, return_exceptions=True)
