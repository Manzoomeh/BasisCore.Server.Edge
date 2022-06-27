import asyncio
from sys import platform
from ..dispatcher.routing_dispatcher import RoutingDispatcher
from bclib.listener import Message


class NamedPipeDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__lock = asyncio.Lock()
        # https://docs.python.org/3/library/sys.html#sys.platform
        if platform == "linux" or platform == "linux2":
            # linux
            from bclib.listener import LinuxNamedPipeListener
            self.__listener = LinuxNamedPipeListener(
                self.options.named_pipe,
                self._on_message_receive_async)
        elif platform == "darwin":
            # OS X
            raise Exception("named pipe not implemented in OS X")
        elif platform == "win32":
            from bclib.listener import WindowsNamedPipeListener
            self.__listener = WindowsNamedPipeListener(
                self.options.named_pipe,
                self._on_message_receive_async)

    async def send_message_async(self, message: Message) -> bool:
        """Send message to endpoint"""

        async with self.__lock:
            return await self.__listener.send_message_async(message)

    def initialize_task(self):
        super().initialize_task()
        self.__listener.initialize_task(self.event_loop)
