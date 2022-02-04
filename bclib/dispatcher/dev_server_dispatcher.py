import asyncio
import signal
from ..dispatcher.socket_dispatcher import RoutingDispatcher
from bclib.listener import Endpoint,  Message, HttpListener


class DevServerDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = HttpListener(
            Endpoint(self.options.server),
            self._on_message_receive)

    async def send_message(self, message: Message) -> bool:
        """Send message to endpoint"""

        ret_val = asyncio.Future()
        ret_val.set_result(None)
        return ret_val

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
