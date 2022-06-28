import asyncio
from ..dispatcher.routing_dispatcher import RoutingDispatcher
from ..listener import Endpoint, Message, SocketListener


class SocketDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__lock = asyncio.Lock()
        self.__listener = SocketListener(
            Endpoint(self.options.receiver),
            Endpoint(self.options.sender),
            self._on_message_receive_async)

    async def send_message_async(self, message: Message) -> bool:
        """Send message to endpoint"""

        async with self.__lock:
            return await self.__listener.send_message_async(message)

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
