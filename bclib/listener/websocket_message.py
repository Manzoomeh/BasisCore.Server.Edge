"""WebSocket Message - Message implementation for WebSocket communications"""
import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType

if TYPE_CHECKING:
    from bclib.listener.websocket_session import WebSocketSession


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


class WSMsg:
    """Internal WebSocket message data structure"""

    def __init__(self,
                 message_type: WSMessageType,
                 text: Optional[str] = None,
                 data: Optional[bytes] = None,
                 extra: Optional[Any] = None):
        self.type = message_type
        self.text = text
        self.data = data
        self.extra = extra

    @property
    def is_text(self) -> bool:
        return self.type == WSMessageType.TEXT

    @property
    def is_binary(self) -> bool:
        return self.type == WSMessageType.BINARY

    @property
    def is_connect(self) -> bool:
        return self.type == WSMessageType.CONNECT

    @property
    def is_disconnect(self) -> bool:
        return self.type == WSMessageType.DISCONNECT

    @property
    def is_close(self) -> bool:
        return self.type == WSMessageType.CLOSE

    @property
    def is_ping(self) -> bool:
        return self.type == WSMessageType.PING

    @property
    def is_pong(self) -> bool:
        return self.type == WSMessageType.PONG

    @property
    def is_error(self) -> bool:
        return self.type == WSMessageType.ERROR

    @property
    def code(self) -> Optional[int]:
        """Get close code"""
        return self.extra if self.is_close and isinstance(self.extra, int) else None

    @property
    def exception(self) -> Optional[Exception]:
        """Get exception for error messages"""
        return self.extra if self.is_error and isinstance(self.extra, Exception) else None

    @classmethod
    def connect(cls) -> 'WSMsg':
        return cls(WSMessageType.CONNECT)

    @classmethod
    def disconnect(cls) -> 'WSMsg':
        return cls(WSMessageType.DISCONNECT)

    @classmethod
    def text(cls, value: str) -> 'WSMsg':
        return cls(WSMessageType.TEXT, text=value)

    @classmethod
    def binary(cls, value: bytes) -> 'WSMsg':
        return cls(WSMessageType.BINARY, data=value)

    @classmethod
    def ping(cls) -> 'WSMsg':
        return cls(WSMessageType.PING)

    @classmethod
    def pong(cls) -> 'WSMsg':
        return cls(WSMessageType.PONG)

    @classmethod
    def close(cls, code: int = 1000) -> 'WSMsg':
        return cls(WSMessageType.CLOSE, extra=code)

    @classmethod
    def error(cls, exception: Exception) -> 'WSMsg':
        return cls(WSMessageType.ERROR, extra=exception)

    def __repr__(self) -> str:
        return f"WSMsg(type={self.type.value}, text={self.text!r}, data_len={len(self.data) if self.data else 0})"


class WebSocketMessage(Message):
    """Message class for WebSocket communications"""

    def __init__(self,
                 message_type: MessageType,
                 session: 'WebSocketSession',
                 ws_message: Optional[WSMsg] = None) -> None:
        """
        Initialize WebSocket Message

        Args:
            session_id: Session identifier
            message_type: Message type
            session: WebSocket session instance
            ws_message: Original WebSocket message object (optional)
        """
        super().__init__(session.session_id, message_type, None)

        self.ws_message = ws_message
        self.session = session

    @property
    def cms_object(self) -> dict:
        """Get CMS object from session"""
        return self.session.cms_object if self.session else {}

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
        return WebSocketMessage(session_id, MessageType.MESSAGE, self.session)

    @property
    def is_text(self) -> bool:
        """Check if message contains text data"""
        return self.ws_message and self.ws_message.is_text

    @property
    def is_binary(self) -> bool:
        """Check if message contains binary data"""
        return self.ws_message and self.ws_message.is_binary

    @property
    def is_connect(self) -> bool:
        """Check if message is a connection event"""
        return self.ws_message and self.ws_message.is_connect

    @property
    def is_disconnect(self) -> bool:
        """Check if message is a disconnection event"""
        return self.ws_message and self.ws_message.is_disconnect

    @property
    def is_close(self) -> bool:
        """Check if message is a close event"""
        return self.ws_message and self.ws_message.is_close

    @property
    def is_ping(self) -> bool:
        """Check if message is a ping"""
        return self.ws_message and self.ws_message.is_ping

    @property
    def is_pong(self) -> bool:
        """Check if message is a pong"""
        return self.ws_message and self.ws_message.is_pong

    @property
    def is_error(self) -> bool:
        """Check if message is an error"""
        return self.ws_message and self.ws_message.is_error

    @property
    def text(self) -> Optional[str]:
        """Get text data from message"""
        return self.ws_message.text if self.ws_message else None

    @property
    def data(self) -> Optional[bytes]:
        """Get binary data from message"""
        return self.ws_message.data if self.ws_message else None

    @staticmethod
    def create_from_websocket(session: 'WebSocketSession',
                              ws_message: WSMsg) -> 'WebSocketMessage':
        """
        Create WebSocketMessage from WebSocket message

        Args:
            session_id: Session identifier
            session: WebSocket session instance
            ws_message: WebSocket message object

        Returns:
            New WebSocketMessage instance
        """
        return WebSocketMessage(
            message_type=MessageType.AD_HOC,
            session=session,
            ws_message=ws_message
        )

    def __repr__(self) -> str:
        msg_type = self.ws_message.type.name if self.ws_message else "NONE"
        return f"WebSocketMessage(session_id={self.session_id[:8]}..., type={msg_type})"
