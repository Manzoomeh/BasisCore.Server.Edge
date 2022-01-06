import asyncio
from .socket_dispatcher import RoutingDispatcher
from listener import EndPoint,  Message
from listener import HttpListener


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = HttpListener(
            EndPoint(self.options.server.ip, self.options.server.port),
            self._on_message_receive)

    def _send_message(self, message: Message) -> None:
        """Send message to endpoint"""
        pass

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')
