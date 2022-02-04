import asyncio
import signal
import threading
from ..dispatcher.routing_dispatcher import RoutingDispatcher
from ..listener import Endpoint, Message, SocketListener


class SocketDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__lock = threading.Lock()
        self.__listener = SocketListener(
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
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda sig, _: loop.stop())
        super().initialize_task(loop)
        self.__listener.initialize_task(loop)
        loop.run_forever()
        tasks = asyncio.all_tasks(loop=loop)
        for t in tasks:
            t.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(group)
        loop.close()
