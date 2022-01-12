import asyncio
import socket
from struct import error
from typing import Callable
from ..listener.message import Message
from ..listener.endpoint import EndPoint


class DuplexSocketListener:
    def __init__(self, receiver: EndPoint, sender: EndPoint, callBack: Callable[[Message], Message]):
        self.__receiver_endpoint = receiver
        self.__sender_endpoint = sender
        self.on_message_receive = callBack
        self.__sender_socket = None

    def send_message(self, message: Message):
        message.write(self.__sender_socket)

    def __start_receiver(self, loop):
        asyncio.set_event_loop(loop)
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receiver:
                    receiver.bind((self.__receiver_endpoint.url,
                                   self.__receiver_endpoint.port))
                    receiver.listen()
                    print(
                        f'Receiver up in {self.__receiver_endpoint.url}:{self.__receiver_endpoint.port} and ready to connect')
                    conn, addr = receiver.accept()
                    print(f'{addr} connect to receiver')

                    with conn:
                        while True:
                            try:
                                message = Message.read(conn)
                                if not message:
                                    break
                            except error as ex:
                                print(f"error in receiver {ex}")
                                break
                            try:
                                self.on_message_receive(message)
                            except error as ex:
                                print(
                                    f"error in process received message {ex}")
            except error as ex:
                print(ex)

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
            receiver_task = loop.run_in_executor(
                None, self.__start_receiver, loop)
            sender_task = loop.run_in_executor(
                None, self.__start_sender, loop)
            await asyncio.gather(receiver_task, sender_task, return_exceptions=True)
