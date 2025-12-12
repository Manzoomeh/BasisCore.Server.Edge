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
        message_handler: IMessageHandler,
        logger: ILogger['TcpListener'],
        options: dict
    ):
        """Initialize TcpListener.

        Args:
            message_handler: Message handler instance
            logger: Logger instance (will be injected by DI if not provided)
            options: Configuration dict with 'endpoint' or 'tcp' key
        """
        self._message_handler = message_handler
        self._logger = logger

        # Normalize options to dict format
        if isinstance(options, str):
            # Simple string: "localhost:3000"
            self.__options = {"endpoint": options}
        elif isinstance(options, dict):
            # Already a dict
            self.__options = options
        else:
            raise ValueError(
                f"Invalid options type: {type(options)}. Expected str or dict.")

        # Extract endpoint from options
        endpoint_value = self.__options.get('endpoint')
        if isinstance(endpoint_value, dict):
            self.__endpoint = Endpoint(endpoint_value.get(
                'host', '127.0.0.1'), endpoint_value.get('port', 3000))
        else:
            self.__endpoint = Endpoint(endpoint_value)
        self.__server: asyncio.Server = None

    def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
        """Schedule the server task on the given event loop."""
        event_loop.create_task(self.__server_task())

    async def __server_task(self):
        """Start the TCP server and accept connections."""
        self.__server = await asyncio.start_server(
            self.__handle_connection_async,
            self.__endpoint.host,
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
