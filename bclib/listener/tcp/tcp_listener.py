"""TCP Listener - handles TCP socket connections"""
import asyncio
from typing import TYPE_CHECKING

from bclib.dispatcher.imessage_handler import IMessageHandler
from bclib.listener import Endpoint
from bclib.listener.ilistener import IListener
from bclib.listener.tcp.tcp_message import TcpMessage
from bclib.logger.ilogger import ILogger


class TcpListener(IListener):
    """Listener that exposes a TCP endpoint backed by TcpMessage."""

    def __init__(
        self,
        endpoint: Endpoint,
        message_handler: IMessageHandler,
        logger: ILogger['TcpListener']
    ):
        """Initialize TcpListener.

        Args:
            endpoint: TCP endpoint (host:port)
            message_handler: Message handler instance
            logger: Logger instance (will be injected by DI if not provided)
        """
        self._message_handler = message_handler
        self._logger = logger
        self.__endpoint = endpoint
        self.__server: asyncio.Server = None

    def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
        """Schedule the server task on the given event loop."""
        event_loop.create_task(self.__server_task())

    async def __server_task(self):
        """Start the TCP server and accept connections."""
        self.__server = await asyncio.start_server(
            self.__handle_connection_async,
            self.__endpoint.url,
            self.__endpoint.port
        )

        addr = self.__server.sockets[0].getsockname()
        if self._logger:
            self._logger.info(
                f'TCP Endpoint server started at {addr[0]}:{addr[1]}')

        async with self.__server:
            await self.__server.serve_forever()

    async def __handle_connection_async(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """Handle an incoming TCP connection and dispatch the message."""
        try:
            message = await TcpMessage.read_from_stream_async(reader, writer)
            if message:
                await self._message_handler.on_message_receive_async(message)
        except Exception as ex:
            if self._logger:
                self._logger.error(f"Error handling endpoint connection: {ex}")
        finally:
            try:
                if writer.can_write_eof():
                    writer.write_eof()
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass  # Best effort cleanup
