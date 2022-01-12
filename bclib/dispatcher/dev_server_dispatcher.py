import asyncio
from ..dispatcher.socket_dispatcher import RoutingDispatcher
from bclib.listener import EndPoint,  Message
from bclib.listener.http_listener import HttpListener


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = HttpListener(
            EndPoint(self.options.server.ip, self.options.server.port),
            self._on_message_receive)

    def _send_message(self, message: Message) -> None:
        """Send message to endpoint"""

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')
