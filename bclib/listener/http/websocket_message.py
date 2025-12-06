"""WebSocket Message Implementation for BasisCore Edge

Provides message types and factory methods for WebSocket communications, supporting
connection lifecycle events (CONNECT, DISCONNECT), data messages (TEXT, BINARY),
and error handling.

Features:
    - Type-safe message creation via factory methods
    - CMS object integration for request context
    - WebSocket session management integration
    - Support for text, binary, close, and error messages
    - Connection lifecycle event handling

Example:
    ```python
    from bclib.listener.http.websocket_message import WebSocketMessage
    from bclib.listener.message_type import MessageType
    
    # Create connection message
    msg = WebSocketMessage.connect(session, MessageType.WEB_SOCKET)
    
    # Create text message
    msg = WebSocketMessage.text_message(session, MessageType.WEB_SOCKET, "Hello")
    
    # Create binary message
    msg = WebSocketMessage.binary_message(session, MessageType.WEB_SOCKET, b"data")
    
    # Check message type
    if msg.is_text:
        print(msg.text)
    ```
"""
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from bclib.listener.icms_base_message import ICmsBaseMessage
from bclib.listener.message import Message
from bclib.listener.message_type import MessageType

if TYPE_CHECKING:
    from bclib.websocket import WebSocketSession


class WSMessageType(Enum):
    """WebSocket message type enumeration

    Defines the different types of WebSocket messages that can be sent or received.
    Used to classify messages in the WebSocket lifecycle and data exchange.

    Attributes:
        CONNECT: Initial connection establishment event
        TEXT: Text data message (UTF-8 string)
        BINARY: Binary data message (bytes)
        CLOSE: WebSocket close frame received
        DISCONNECT: Connection termination event
        ERROR: Error occurred during communication
    """
    CONNECT = "connect"
    TEXT = "text"
    BINARY = "binary"
    CLOSE = "close"
    DISCONNECT = "disconnect"
    ERROR = "error"


class WebSocketMessage(Message, ICmsBaseMessage):
    """Message class for WebSocket communications

    Represents a WebSocket message with type information, session context, and data payload.
    Integrates with BasisCore's CMS-based message handling and dispatcher system.

    Attributes:
        session_id (str): Unique identifier for the WebSocket session
        session (WebSocketSession): WebSocket session instance
        ws_type (WSMessageType): WebSocket-specific message type

    Example:
        ```python
        # Use factory methods instead of direct instantiation
        msg = WebSocketMessage.connect(session, MessageType.WEB_SOCKET)
        msg = WebSocketMessage.text_message(session, MessageType.WEB_SOCKET, "data")
        msg = WebSocketMessage.binary_message(session, MessageType.WEB_SOCKET, b"data")
        msg = WebSocketMessage.close_message(session, MessageType.WEB_SOCKET, 1000)
        msg = WebSocketMessage.disconnect(session, MessageType.WEB_SOCKET, 1000)
        msg = WebSocketMessage.error(session, MessageType.WEB_SOCKET, exception)
        ```
    """

    def __init__(self,
                 message_type: MessageType,
                 session: 'WebSocketSession',
                 ws_message_type: WSMessageType,
                 text: Optional[str] = None,
                 data: Optional[bytes] = None,
                 extra: Optional[Any] = None) -> None:
        """Initialize WebSocket message

        Args:
            message_type (MessageType): Message type for dispatcher routing
            session (WebSocketSession): WebSocket session instance
            ws_message_type (WSMessageType): WebSocket message type (CONNECT, TEXT, etc.)
            text (Optional[str]): Text data for TEXT messages. Defaults to None.
            data (Optional[bytes]): Binary data for BINARY messages. Defaults to None.
            extra (Optional[Any]): Extra data - close code for CLOSE/DISCONNECT,
                exception for ERROR messages. Defaults to None.

        Note:
            Prefer using factory methods (connect, text_message, etc.) instead of
            direct instantiation for better type safety and clarity.
        """
        # WebSocketMessage needs session_id and type for dispatcher
        self.session_id = session.session_id
        self._type = message_type
        self.session = session
        self.ws_type = ws_message_type
        self._text = text
        self._data = data
        self._extra = extra

    @property
    def type(self) -> MessageType:
        """Get message type for dispatcher routing

        Returns:
            MessageType: The message type used by dispatcher for routing
        """
        return self._type

    @property
    def cms_object(self) -> dict:
        """Get CMS object from WebSocket session

        Returns:
            dict: CMS object containing request context and metadata
        """
        return self.session.cms_object

    # ==================== Type Check Properties ====================

    @property
    def is_text(self) -> bool:
        """Check if message contains text data

        Returns:
            bool: True if message type is TEXT, False otherwise
        """
        return self.ws_type == WSMessageType.TEXT

    @property
    def is_binary(self) -> bool:
        """Check if message contains binary data

        Returns:
            bool: True if message type is BINARY, False otherwise
        """
        return self.ws_type == WSMessageType.BINARY

    @property
    def is_connect(self) -> bool:
        """Check if message is a connection event

        Returns:
            bool: True if message type is CONNECT, False otherwise
        """
        return self.ws_type == WSMessageType.CONNECT

    @property
    def is_disconnect(self) -> bool:
        """Check if message is a disconnection event

        Returns:
            bool: True if message type is DISCONNECT, False otherwise
        """
        return self.ws_type == WSMessageType.DISCONNECT

    @property
    def is_close(self) -> bool:
        """Check if message is a close event

        Returns:
            bool: True if message type is CLOSE, False otherwise
        """
        return self.ws_type == WSMessageType.CLOSE

    @property
    def is_error(self) -> bool:
        """Check if message is an error

        Returns:
            bool: True if message type is ERROR, False otherwise
        """
        return self.ws_type == WSMessageType.ERROR

    # ==================== Data Access Properties ====================

    @property
    def text(self) -> Optional[str]:
        """Get text data from message

        Returns:
            Optional[str]: Text data if message is TEXT type, None otherwise
        """
        return self._text

    @property
    def binary(self) -> Optional[bytes]:
        """Get binary data from message

        Returns:
            Optional[bytes]: Binary data if message is BINARY type, None otherwise
        """
        return self._data

    @property
    def code(self) -> Optional[int]:
        """Get WebSocket close code

        Returns:
            Optional[int]: Close code for CLOSE messages, None otherwise
        """
        return self._extra if self.is_close and isinstance(self._extra, int) else None

    @property
    def exception(self) -> Optional[Exception]:
        """Get exception for error messages

        Returns:
            Optional[Exception]: Exception object for ERROR messages, None otherwise
        """
        return self._extra if self.is_error and isinstance(self._extra, Exception) else None

    # ==================== Factory Methods ====================

    @classmethod
    def connect(cls, session: 'WebSocketSession', message_type: MessageType) -> 'WebSocketMessage':
        """Create CONNECT message for new WebSocket connection

        Args:
            session (WebSocketSession): WebSocket session instance
            message_type (MessageType): Message type for dispatcher routing

        Returns:
            WebSocketMessage: CONNECT message instance
        """
        return cls(message_type, session, WSMessageType.CONNECT)

    @classmethod
    def disconnect(cls, session: 'WebSocketSession', message_type: MessageType, code: int) -> 'WebSocketMessage':
        """Create DISCONNECT message for connection termination

        Args:
            session (WebSocketSession): WebSocket session instance
            message_type (MessageType): Message type for dispatcher routing
            code (int): WebSocket close code

        Returns:
            WebSocketMessage: DISCONNECT message instance
        """
        return cls(message_type, session, WSMessageType.DISCONNECT, extra=code)

    @classmethod
    def text_message(cls, session: 'WebSocketSession', message_type: MessageType, value: str) -> 'WebSocketMessage':
        """Create TEXT message with string data

        Args:
            session (WebSocketSession): WebSocket session instance
            message_type (MessageType): Message type for dispatcher routing
            value (str): Text data to send

        Returns:
            WebSocketMessage: TEXT message instance
        """
        return cls(message_type, session, WSMessageType.TEXT, text=value)

    @classmethod
    def binary_message(cls, session: 'WebSocketSession', message_type: MessageType, value: bytes) -> 'WebSocketMessage':
        """Create BINARY message with bytes data

        Args:
            session (WebSocketSession): WebSocket session instance
            message_type (MessageType): Message type for dispatcher routing
            value (bytes): Binary data to send

        Returns:
            WebSocketMessage: BINARY message instance
        """
        return cls(message_type, session, WSMessageType.BINARY, data=value)

    @classmethod
    def close_message(cls, session: 'WebSocketSession', message_type: MessageType, code: int = 1000) -> 'WebSocketMessage':
        """Create CLOSE message for WebSocket close frame

        Args:
            session (WebSocketSession): WebSocket session instance
            message_type (MessageType): Message type for dispatcher routing
            code (int): WebSocket close code. Defaults to 1000 (normal closure).

        Returns:
            WebSocketMessage: CLOSE message instance
        """
        return cls(message_type, session, WSMessageType.CLOSE, extra=code)

    @classmethod
    def error(cls, session: 'WebSocketSession', message_type: MessageType, exception: Exception) -> 'WebSocketMessage':
        """Create ERROR message for exception handling

        Args:
            session (WebSocketSession): WebSocket session instance
            message_type (MessageType): Message type for dispatcher routing
            exception (Exception): Exception that occurred

        Returns:
            WebSocketMessage: ERROR message instance
        """
        return cls(message_type, session, WSMessageType.ERROR, extra=exception)

    async def set_response_async(self, cms_object: dict) -> None:
        """Set response data - WebSocket handles responses through session, not message

        Args:
            cms_object: The CMS object containing response data (not used for WebSocket)
        """
        # WebSocket responses are sent through session.send_* methods, not via message
        pass

    def __repr__(self) -> str:
        return f"WebSocketMessage(session_id={self.session_id[:8]}..., type={self.ws_type.name})"
