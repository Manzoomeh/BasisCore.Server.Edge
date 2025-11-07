"""WebSocket Context - context for WebSocket-based requests"""
from typing import TYPE_CHECKING

from bclib.context.request_context import RequestContext

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher
    from bclib.dispatcher.websocket_session import WebSocketSession
    from bclib.dispatcher.websocket_session_manager import \
        WebSocketSessionManager
    from bclib.listener.websocket_message import WebSocketMessage


class WebSocketContext(RequestContext):
    """Context class for WebSocket-based requests"""

    def __init__(self,
                 cms_object: dict,
                 dispatcher: 'IDispatcher',
                 ws_message: 'WebSocketMessage') -> None:
        """
        Initialize WebSocket context

        Args:
            cms_object: CMS object containing request data
            dispatcher: Dispatcher instance
            ws_message: WebSocket message instance
        """
        super().__init__(cms_object, dispatcher)
        self.message: WebSocketMessage = ws_message
        self.session: WebSocketSession = ws_message.session
        self.session_manager: WebSocketSessionManager = self.session.session_manager
        self.is_adhoc = False

    def __repr__(self) -> str:
        return f"WebSocketContext(session_id={self.session.session_id[:8]}..., message_type={self.message_type}, url={self.url})"
