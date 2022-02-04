import asyncio
from typing import Callable

from ..http_listener.MultiThreadHTTPServer import MultiThreadHTTPServer
from ..http_listener.edge_http_request_handler import EdgeHTTPRequestHandler
from ..message import Message
from ..endpoint import Endpoint


class HttpListener:
    def __init__(self, endpoint: Endpoint, callback: 'Callable[[Message], Message]'):
        self.__endpoint = endpoint
        self.on_message_receive = callback
        self.__web_server = MultiThreadHTTPServer(
            (self.__endpoint.url,  self.__endpoint.port), EdgeHTTPRequestHandler)
        self.__web_server.on_message_receive = self.on_message_receive

    def initialize_task(self, loop: asyncio.AbstractEventLoop):
        loop.create_task(self.__server_task())

    async def __server_task(self):
        loop = asyncio.get_running_loop()
        print(
            f"Development Edge server started at http://{self.__endpoint.url}:{self.__endpoint.port}")
        loop.run_in_executor(None, self.__web_server.serve_forever)
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.__web_server.shutdown()
            print("Development Edge server stopped.")
