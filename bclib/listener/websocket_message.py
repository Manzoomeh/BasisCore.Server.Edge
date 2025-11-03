"""WebSocket Message - Message implementation for WebSocket communications"""
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType

if TYPE_CHECKING:
    from bclib.dispatcher.websocket_session import WebSocketSession


class WSMessageType(Enum):
    """WebSocket message types"""
    CONNECT = "connect"
    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"
    DISCONNECT = "disconnect"
    ERROR = "error"


class WebSocketMessage(Message):
    """Message class for WebSocket communications"""

    def __init__(self,
                 message_type: MessageType,
                 session: 'WebSocketSession',
                 ws_message_type: WSMessageType,
                 text: Optional[str] = None,
                 data: Optional[bytes] = None,
                 extra: Optional[Any] = None) -> None:
        """
        Initialize WebSocket Message

        Args:
            message_type: Message type for dispatcher
            session: WebSocket session instance
            ws_message_type: WebSocket message type (CONNECT, TEXT, etc.)
            text: Text data (for TEXT messages)
            data: Binary data (for BINARY messages)
            extra: Extra data (code for CLOSE, exception for ERROR)
        """
        super().__init__(session.session_id, message_type, None)

        self.session = session
        self.ws_type = ws_message_type
        self._text = text
        self._data = data
        self._extra = extra

    @property
    def cms_object(self) -> dict:
        """Get CMS object from session"""
        return self.session.cms_object if self.session else {}

    # ==================== Type Check Properties ====================

    @property
    def is_text(self) -> bool:
        """Check if message contains text data"""
        return self.ws_type == WSMessageType.TEXT

    @property
    def is_binary(self) -> bool:
        """Check if message contains binary data"""
        return self.ws_type == WSMessageType.BINARY

    @property
    def is_connect(self) -> bool:
        """Check if message is a connection event"""
        return self.ws_type == WSMessageType.CONNECT

    @property
    def is_disconnect(self) -> bool:
        """Check if message is a disconnection event"""
        return self.ws_type == WSMessageType.DISCONNECT

    @property
    def is_close(self) -> bool:
        """Check if message is a close event"""
        return self.ws_type == WSMessageType.CLOSE

    @property
    def is_ping(self) -> bool:
        """Check if message is a ping"""
        return self.ws_type == WSMessageType.PING

    @property
    def is_pong(self) -> bool:
        """Check if message is a pong"""
        return self.ws_type == WSMessageType.PONG

    @property
    def is_error(self) -> bool:
        """Check if message is an error"""
        return self.ws_type == WSMessageType.ERROR

    # ==================== Data Access Properties ====================

    @property
    def text(self) -> Optional[str]:
        """Get text data from message"""
        return self._text

    @property
    def binary(self) -> Optional[bytes]:
        """Get binary data from message"""
        return self._data

    @property
    def code(self) -> Optional[int]:
        """Get close code"""
        return self._extra if self.is_close and isinstance(self._extra, int) else None

    @property
    def exception(self) -> Optional[Exception]:
        """Get exception for error messages"""
        return self._extra if self.is_error and isinstance(self._extra, Exception) else None

    # ==================== Factory Methods ====================

    @classmethod
    def connect(cls, session: 'WebSocketSession', message_type: MessageType) -> 'WebSocketMessage':
        """Create CONNECT message"""
        return cls(message_type, session, WSMessageType.CONNECT)

    @classmethod
    def disconnect(cls, session: 'WebSocketSession', message_type: MessageType, code: int) -> 'WebSocketMessage':
        """Create DISCONNECT message"""
        return cls(message_type, session, WSMessageType.DISCONNECT, extra=code)

    @classmethod
    def text_message(cls, session: 'WebSocketSession', message_type: MessageType, value: str) -> 'WebSocketMessage':
        """Create TEXT message"""
        return cls(message_type, session, WSMessageType.TEXT, text=value)

    @classmethod
    def binary_message(cls, session: 'WebSocketSession', message_type: MessageType, value: bytes) -> 'WebSocketMessage':
        """Create BINARY message"""
        return cls(message_type, session, WSMessageType.BINARY, data=value)

    @classmethod
    def ping(cls, session: 'WebSocketSession', message_type: MessageType) -> 'WebSocketMessage':
        """Create PING message"""
        return cls(message_type, session, WSMessageType.PING)

    @classmethod
    def pong(cls, session: 'WebSocketSession', message_type: MessageType) -> 'WebSocketMessage':
        """Create PONG message"""
        return cls(message_type, session, WSMessageType.PONG)

    @classmethod
    def close_message(cls, session: 'WebSocketSession', message_type: MessageType, code: int = 1000) -> 'WebSocketMessage':
        """Create CLOSE message"""
        return cls(message_type, session, WSMessageType.CLOSE, extra=code)

    @classmethod
    def error(cls, session: 'WebSocketSession', message_type: MessageType, exception: Exception) -> 'WebSocketMessage':
        """Create ERROR message"""
        return cls(message_type, session, WSMessageType.ERROR, extra=exception)

    def create_response_message(self, session_id: str, cms_object: dict) -> "WebSocketMessage":
        """
        Create a response message

        Args:
            session_id: Session identifier
            cms_object: CMS object for response (deprecated, uses session instead)

        Returns:
            New WebSocketMessage instance
        """
        if not self.session:
            raise ValueError("Cannot create response message without session")
        return WebSocketMessage(MessageType.MESSAGE, self.session, WSMessageType.TEXT)

    def __repr__(self) -> str:
        return f"WebSocketMessage(session_id={self.session_id[:8]}..., type={self.ws_type.name})"
