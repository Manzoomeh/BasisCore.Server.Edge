import threading
from ..dispatcher.routing_dispatcher import RoutingDispatcher
from bclib.listener import Message, WindowsNamedPipeListener


class NamedPipeDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__lock = threading.Lock()
        self.__listener = WindowsNamedPipeListener(
            self.options.named_pipe,
            self._on_message_receive_async)

    async def send_message_async(self, message: Message) -> bool:
        """Send message to endpoint"""

        try:
            self.__lock.acquire()
            return await self.__listener.send_message_async(message)
        finally:
            self.__lock.release()

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
