import asyncio
from ..dispatcher.routing_dispatcher import RoutingDispatcher
from ..listener import EndPoint, DuplexSocketListener, Message


class SocketDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = DuplexSocketListener(
            EndPoint(self.options.receiver.ip, self.options.receiver.port),
            EndPoint(self.options.sender.ip, self.options.sender.port),
            self._on_message_receive)

    def _send_message(self, message: Message) -> None:
        """Send message to endpoint"""

        self.__listener.send_message(message)

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')
