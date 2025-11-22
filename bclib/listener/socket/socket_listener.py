"""Socket Listener - handles TCP socket connections"""
import asyncio
from typing import TYPE_CHECKING, Awaitable, Callable

from bclib.listener import Endpoint
from bclib.listener.ilistener import IListener
from bclib.listener.socket.socket_message import SocketMessage

if TYPE_CHECKING:
    from bclib.listener import Message


class SocketListener(IListener):
    """
    TCP Socket Listener for handling TCP connections with custom binary protocol

    This listener opens a TCP server that accepts incoming connections and
    processes messages using the SocketMessage binary protocol.

    Features:
        - TCP server on specified host:port
        - Custom binary protocol message handling
        - Async message processing with callback
        - Automatic connection lifecycle management

    Example:
        ```python
        from bclib import edge

        options = {
            "endpoint": "localhost:8080"
        }

        app = edge.from_options(options)

        @app.restful_action()
        async def handler(context):
            return {"message": "Hello from endpoint"}

        app.listening()
        ```
    """

    def __init__(
        self,
        endpoint: Endpoint,
        on_message_receive_async: Callable[['Message'], Awaitable[None]]
    ):
        """
        Initialize SocketListener

        Args:
            endpoint: Endpoint configuration (host:port)
            on_message_receive_async: Async callback to process received messages
        """
        super().__init__(on_message_receive_async)
        self.__endpoint = endpoint
        self.__server: asyncio.Server = None

    def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
        """
        Initialize the TCP server task

        Args:
            event_loop: asyncio event loop to run the server on
        """
        event_loop.create_task(self.__server_task())

    async def __server_task(self):
        """Start TCP server and handle connections"""
        self.__server = await asyncio.start_server(
            self.__handle_connection_async,
            self.__endpoint.url,
            self.__endpoint.port
        )

        addr = self.__server.sockets[0].getsockname()
        print(f'TCP Endpoint server started at {addr[0]}:{addr[1]}')

        async with self.__server:
            await self.__server.serve_forever()

    async def __handle_connection_async(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """
        Handle incoming TCP connection

        Reads message from stream, processes it through dispatcher which sets
        the response on the message object, then writes the response back to stream.

        Args:
            reader: asyncio StreamReader for reading incoming data
            writer: asyncio StreamWriter for sending response

        Note:
            The dispatcher calls message.set_response_async() which automatically
            writes the response to the TCP stream. No explicit response writing needed.
        """
        try:
            # Read message from stream
            message = await SocketMessage.read_from_stream_async(reader, writer)

            if message:
                # Process message through dispatcher - response is written automatically
                await self._on_message_receive(message)
        except Exception as ex:
            print(f"Error handling endpoint connection: {ex}")
        finally:
            # Close connection
            try:
                if writer.can_write_eof():
                    writer.write_eof()
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass  # Best effort cleanup
