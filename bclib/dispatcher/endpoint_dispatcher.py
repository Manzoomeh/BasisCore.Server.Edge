import asyncio

from ..listener import Endpoint, Message
from .routing_dispatcher import RoutingDispatcher


class EndpointDispatcher(RoutingDispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__endpoint = Endpoint(self.options.endpoint)

    def send_message_async(self, message: Message) -> bool:
        """Send message to endpoint"""
        return False

    def initialize_task(self):
        super().initialize_task()

        async def on_connection_open(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            msg = await Message.read_from_stream_async(reader)
            result = await self._on_message_receive_async(msg)
            await result.write_to_stream_async(writer)
            if writer.can_write_eof():
                writer.write_eof()
            await writer.drain()
            writer.close()

        async def start_servers_async():
            server = await asyncio.start_server(on_connection_open, self.__endpoint.url, self.__endpoint.port,)
            print(
                f'Server up in {self.__endpoint.url}:{self.__endpoint.port} and wait for client connection...')
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            print("Server shutdown...")
            server.close()

        self.event_loop.create_task(start_servers_async())
