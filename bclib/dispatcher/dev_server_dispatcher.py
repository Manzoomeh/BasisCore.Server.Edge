import asyncio
from ..dispatcher.socket_dispatcher import RoutingDispatcher
from bclib.listener import Endpoint,  Message, HttpListener


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = HttpListener(
            Endpoint(self.options.server),
            self._on_message_receive_async)

    async def send_message_async(self, message: Message) -> bool:
        """Send message to endpoint"""

        ret_val = asyncio.Future()
        ret_val.set_result(None)
        return ret_val

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
