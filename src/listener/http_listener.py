from typing import Callable
from http.server import HTTPServer

from .edge_http_request_handler import EdgeHTTPRequestHandler

from .message import Message
from .endpoint import EndPoint


class HttpListener:
    def __init__(self, endpoint: EndPoint, callBack: Callable[[Message], Message]):
        self.__endpoint = endpoint
        self.on_message_receive = callBack

    async def process_async(self):
        webServer = HTTPServer(
            (self.__endpoint.url,  self.__endpoint.port), EdgeHTTPRequestHandler)
        webServer.on_message_receive = self.on_message_receive
        print(
            f"Development Edge server started at http://{self.__endpoint.url}:{self.__endpoint.port}")

        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

        webServer.server_close()
        print("Development Edge server stopped.")
