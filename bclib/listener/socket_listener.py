import asyncio
import socket
import json
from struct import error
from typing import Callable
from ..listener.endpoint import EndPoint


class SocketListener:
    def __init__(self, endpoint: EndPoint, callBack: 'Callable[[bytes], bytes]'):
        self.__endPoint = endpoint
        self.__callback = callBack

    async def __start_receiver_async(self):
        def MessageHandler(conn, loop):
            asyncio.set_event_loop(loop)
            with conn:
                responce = None
                try:
                    request = SocketListener.__read_from_socket(conn)
                    if request:
                        responce = self.__callback(request)
                except error as e:
                    print(repr(e))
                    responce = SocketListener.__convert_to_responce(e)
                SocketListener.__write_to_socket(conn, responce)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.__endPoint.url, self.__endPoint.port))
            s.listen()
            print(
                f'Host service is up and ready to connect in {self.__endPoint.url}:{self.__endPoint.port}')

            loop = asyncio.get_event_loop()
            while True:
                conn, _ = s.accept()
                loop.run_in_executor(None, MessageHandler, conn, loop)

    @staticmethod
    def __convert_to_responce(er: Exception):
        data = {
            'cms':
            {
                'content': f'<html><head><title>{str(er)}</title></head><body>{repr(er)}</body></html>',
                'webserver':
                {
                    'index': '5',
                    'headercode': '500 Internal Server Error'
                }
            }
        }
        return json.dumps(data).encode("utf-8")

    @staticmethod
    def __read_from_socket(connection: socket.socket):
        message_length_in_byte = connection.recv(4)
        message_length = int.from_bytes(
            message_length_in_byte, byteorder='little', signed=True)
        return connection.recv(message_length)

    @staticmethod
    def __write_to_socket(connection: socket.socket, data: list):
        connection.send(data)

    async def process_async(self):
        while True:
            await asyncio.create_task(self.__start_receiver_async())
