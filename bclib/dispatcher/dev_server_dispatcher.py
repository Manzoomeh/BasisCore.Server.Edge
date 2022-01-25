import asyncio
from ..dispatcher.socket_dispatcher import RoutingDispatcher
from bclib.listener import Endpoint,  Message, HttpListener


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = HttpListener(
            Endpoint(self.options.server),
            self._on_message_receive)

    def send_message(self, message: Message) -> bool:
        """Send message to endpoint"""

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')
