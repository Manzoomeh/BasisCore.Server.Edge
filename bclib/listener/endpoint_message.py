"""Endpoint Message - handles TCP endpoint communication with custom binary protocol"""
import asyncio
from typing import Optional

from .message import Message
from .message_type import MessageType


class EndpointMessage(Message):
    """
    Message class for TCP endpoint communication using custom binary protocol

    This class handles bidirectional communication over TCP streams using a custom
    binary protocol format for message serialization and deserialization.

    Protocol Format:
        - 1 byte: Message type (MessageType enum value)
        - 4 bytes: Session ID length (big-endian signed integer)
        - N bytes: Session ID string (UTF-8 encoded)
        - 4 bytes: Payload length (big-endian signed integer) - only for certain message types
        - N bytes: Payload data - only for certain message types

    Supported Message Types with Payload:
        - AD_HOC: Ad-hoc request/response messages
        - MESSAGE: Regular messages
        - CONNECT: Connection establishment messages

    Attributes:
        reader: asyncio StreamReader for reading from TCP stream
        writer: asyncio StreamWriter for writing to TCP stream

    Example:
        ```python
        # Server side - read incoming message
        async def handle_client(reader, writer):
            message = await EndpointMessage.read_from_stream_async(reader, writer)
            if message:
                print(f"Received: {message.type}, Session: {message.session_id}")

                # Process and send response
                response = await dispatcher.on_message_receive_async(message)
                await response.write_to_stream_async(writer)

        # Client side - send message and read response
        reader, writer = await asyncio.open_connection('localhost', 8080)
        message = EndpointMessage(reader, writer, session_id, MessageType.AD_HOC, payload)
        await message.write_to_stream_async(writer)
        response = await message.read_next_message_async()
        ```
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        session_id: str,
        message_type: MessageType,
        buffer: Optional[bytes] = None
    ) -> None:
        """
        Initialize EndpointMessage

        Args:
            reader: asyncio StreamReader for reading from stream
            writer: asyncio StreamWriter for writing to stream
            session_id: Unique session identifier
            message_type: Type of message (from MessageType enum)
            buffer: Optional message payload bytes
        """
        super().__init__(session_id, message_type, buffer)
        self.reader = reader
        self.writer = writer

    async def read_next_message_async(self) -> Optional['EndpointMessage']:
        """
        Read the next message from the stream using the same reader/writer

        Returns:
            Next EndpointMessage from stream, or None if stream ended

        Example:
            ```python
            message = await EndpointMessage.read_from_stream_async(reader, writer)
            next_message = await message.read_next_message_async()
            ```
        """
        return await EndpointMessage.read_from_stream_async(self.reader, self.writer)

    @staticmethod
    async def read_from_stream_async(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> Optional['EndpointMessage']:
        """
        Read and parse a message from TCP stream using custom binary protocol

        Protocol parsing steps:
            1. Read 1 byte for message type
            2. Read 4 bytes for session ID length
            3. Read session ID string (UTF-8)
            4. For specific message types (AD_HOC, MESSAGE, CONNECT):
               - Read 4 bytes for payload length
               - Read payload data

        Args:
            reader: asyncio StreamReader to read from
            writer: asyncio StreamWriter for response (stored in message)

        Returns:
            Parsed EndpointMessage or None if stream ended

        Raises:
            asyncio.IncompleteReadError: If stream ends before reading expected bytes
            UnicodeDecodeError: If session ID is not valid UTF-8

        Example:
            ```python
            async def handle_connection(reader, writer):
                try:
                    message = await EndpointMessage.read_from_stream_async(reader, writer)
                    if message:
                        print(f"Type: {message.type}, Session: {message.session_id}")
                except asyncio.IncompleteReadError:
                    print("Connection closed unexpectedly")
            ```
        """
        message: Optional[EndpointMessage] = None

        # Read message type (1 byte)
        data = await reader.readexactly(1)
        if data:
            message_type = MessageType(int.from_bytes(
                data, byteorder='big', signed=True))

            # Read session ID length (4 bytes)
            data = await reader.readexactly(4)
            session_id_len = int.from_bytes(data, byteorder='big', signed=True)

            # Read session ID string
            data = await reader.readexactly(session_id_len)
            session_id = data.decode("utf-8")

            # Read payload for specific message types
            payload = None
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                # Read payload length (4 bytes)
                data = await reader.readexactly(4)
                payload_len = int.from_bytes(
                    data, byteorder='big', signed=True)

                # Read payload data
                data = await reader.readexactly(payload_len)
                payload = data

            message = EndpointMessage(
                reader, writer, session_id, message_type, payload)

        return message
