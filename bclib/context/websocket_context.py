"""WebSocket Context - context for WebSocket-based requests"""
from typing import TYPE_CHECKING

from listener.websocket_message import WebSocketMessage
from listener.websocket_session import WebSocketSession

from bclib.context.request_context import RequestContext

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher
    from bclib.listener.websocket_message import WebSocketMessage
    from bclib.listener.websocket_session import WebSocketSession


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
        self.ws_message: 'WebSocketMessage' = ws_message
        self.session: 'WebSocketSession' = ws_message.session
        self.is_adhoc = False

    def __repr__(self) -> str:
        return f"WebSocketContext(session_id={self.session.session_id[:8]}..., message_type={self.message_type}, url={self.url})"
