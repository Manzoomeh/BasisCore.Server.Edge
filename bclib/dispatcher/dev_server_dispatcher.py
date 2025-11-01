import asyncio

from bclib.listener import Endpoint, HttpListener

from ..dispatcher.socket_dispatcher import RoutingDispatcher


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self, options: dict, loop: asyncio.AbstractEventLoop = None):
        super().__init__(options=options, loop=loop)
        self.__listener = HttpListener(
            Endpoint(self.options.server),
            self._on_message_receive_async,
            self.options.ssl,
            self.options.configuration,
            self.ws_manager
        )

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
