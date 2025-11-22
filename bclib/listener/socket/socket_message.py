"""Socket Message - handles TCP socket communication with custom binary protocol"""
import asyncio
import json
from typing import Any, Optional

from bclib.listener.icms_base_message import ICmsBaseMessage
from bclib.listener.iresponse_base_message import IResponseBaseMessage
from bclib.listener.message import Message
from bclib.listener.message_type import MessageType


class SocketMessage(Message, ICmsBaseMessage, IResponseBaseMessage):
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
            message = await SocketMessage.read_from_stream_async(reader, writer)
            if message:
                print(f"Received: {message.type}, Session: {message.session_id}")

                # Dispatcher processes message and sets response asynchronously
                await dispatcher.on_message_receive_async(message)

                # Response has been set in message.buffer, write it back
                await message.write_to_stream_async(writer)

        # Client side - send message and read response
        reader, writer = await asyncio.open_connection('localhost', 8080)
        message = SocketMessage(reader, writer, session_id, MessageType.AD_HOC, payload)
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
        Initialize SocketMessage

        Args:
            reader: asyncio StreamReader for reading from stream
            writer: asyncio StreamWriter for writing to stream
            session_id: Unique session identifier
            message_type: Type of message (from MessageType enum)
            buffer: Optional message payload bytes
        """
        # EndpointMessage needs session_id and type for binary protocol
        self.session_id = session_id
        self._type = message_type
        self.reader = reader
        self.writer = writer
        self.buffer = buffer

    @property
    def type(self) -> MessageType:
        """Get message type"""
        return self._type

    @property
    def cms_object(self) -> dict:
        """Get CMS object from buffer"""
        if self.buffer:
            try:
                return json.loads(self.buffer.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}
        return {}

    async def set_response_async(self, cms_object: dict) -> None:
        """Set response data and write to stream asynchronously

        This method encodes the response data to JSON and writes it to the TCP stream.
        Called by the dispatcher after processing the request.

        Args:
            cms_object: The CMS object containing response data
        """
        import json
        if cms_object is not None:
            buffer = json.dumps(cms_object).encode('utf-8')
            await self._write_to_stream_async(self.writer, self.session_id, self.type, buffer)

    async def read_next_message_async(self) -> Optional['SocketMessage']:
        """
        Read the next message from this connection's stream

        Returns:
            Next SocketMessage from stream, or None if stream ended

        Example:
            ```python
            message = await SocketMessage.read_from_stream_async(reader, writer)
            next_message = await message.read_next_message_async()
            ```
        """
        return await SocketMessage.read_from_stream_async(self.reader, self.writer)

    @staticmethod
    async def read_from_stream_async(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> Optional['SocketMessage']:
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
            Parsed SocketMessage or None if stream ended

        Raises:
            asyncio.IncompleteReadError: If stream ends before reading expected bytes
            UnicodeDecodeError: If session ID is not valid UTF-8

        Example:
            ```python
            async def handle_connection(reader, writer):
                try:
                    message = await SocketMessage.read_from_stream_async(reader, writer)
                    if message:
                        print(f"Type: {message.type}, Session: {message.session_id}")
                except asyncio.IncompleteReadError:
                    print("Connection closed unexpectedly")
            ```
        """
        message: Optional[SocketMessage] = None

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

            message = SocketMessage(
                reader, writer, session_id, message_type, payload)

        return message

    @staticmethod
    async def _write_to_stream_async(
        writer: asyncio.StreamWriter,
        session_id: str,
        message_type: MessageType,
        buffer: Optional[bytes]
    ) -> bool:
        """Static helper to write message to TCP stream using binary protocol

        Args:
            writer: asyncio StreamWriter to write to
            session_id: Session identifier
            message_type: Type of message
            buffer: Optional message payload bytes

        Returns:
            True if sent successfully, False if cancelled
        """
        is_send = True
        try:
            # Write message type (1 byte)
            writer.write(message_type.value.to_bytes(1, 'big'))

            # Write session ID length and data
            session_id_data = session_id.encode('utf-8')
            writer.write(len(session_id_data).to_bytes(4, 'big'))
            writer.write(session_id_data)

            # Write payload for specific message types
            if message_type in (MessageType.AD_HOC, MessageType.MESSAGE, MessageType.CONNECT):
                if buffer:
                    writer.write(len(buffer).to_bytes(4, 'big'))
                    writer.write(buffer)
                else:
                    writer.write((0).to_bytes(4, 'big'))  # Zero length payload

            await writer.drain()
        except asyncio.CancelledError:
            is_send = False
        return is_send

    async def write_to_stream_async(self, writer: asyncio.StreamWriter) -> bool:
        """Write this message to TCP stream using binary protocol

        Args:
            writer: asyncio StreamWriter to write to

        Returns:
            True if sent successfully, False if cancelled

        Example:
            ```python
            response = SocketMessage(reader, writer, session_id, MessageType.AD_HOC, data)
            success = await response.write_to_stream_async(writer)
            ```
        """
        return await SocketMessage._write_to_stream_async(writer, self.session_id, self.type, self.buffer)
