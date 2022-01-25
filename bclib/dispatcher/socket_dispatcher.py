import asyncio
import threading
from ..dispatcher.routing_dispatcher import RoutingDispatcher
from ..listener import Endpoint, DuplexSocketListener, Message


class SocketDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__lock = threading.Lock()
        self.__listener = DuplexSocketListener(
            Endpoint(self.options.receiver),
            Endpoint(self.options.sender),
            self._on_message_receive)

    def send_message(self, message: Message) -> bool:
        """Send message to endpoint"""

        try:
            self.__lock.acquire()
            return self.__listener.send_message(message)
        finally:
            self.__lock.release()

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')
