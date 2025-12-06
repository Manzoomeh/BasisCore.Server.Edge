"""
WebSocket Context - Context for WebSocket-based requests

This module provides the WebSocketContext class for handling WebSocket connections in the BasisCore.Server.Edge framework.
It extends CmsBaseContext to provide WebSocket-specific functionality including session management,
message handling, and bidirectional communication.

Key Features:
    - WebSocket session management with unique session IDs
    - Access to session manager for broadcasting and session control
    - Message type detection (text, binary, close, ping, pong)
    - Bidirectional real-time communication
    - Integration with CMS message format

Example:
    ```python
    @app.websocket_handler(app.url("ws/chat"))
    async def chat_handler(context: WebSocketContext):
        # Access session information
        session_id = context.session.session_id
        
        # Send message to current session
        await context.session.send_text({"message": "Hello!"})
        
        # Broadcast to all sessions
        await context.session_manager.broadcast({
            "user": session_id,
            "message": context.body.get("text")
        })
        
        # Access WebSocket message details
        message_type = context.message.message_type
        payload = context.message.payload
    ```
"""
from typing import TYPE_CHECKING

from bclib.dispatcher.idispatcher import IDispatcher
from bclib.listener import (WebSocketMessage, WebSocketSession,
                            WebSocketSessionManager)

from .cms_base_context import CmsBaseContext


class WebSocketContext(CmsBaseContext):
    """
    Context class for WebSocket-based requests

    Provides WebSocket-specific functionality for handling real-time bidirectional
    communication between client and server. Each WebSocket connection gets its own
    session with a unique ID and access to the session manager for broadcasting.

    Attributes:
        message (WebSocketMessage): The WebSocket message object containing payload and metadata
        session (WebSocketSession): The WebSocket session for this connection
        session_manager (WebSocketSessionManager): Manager for all WebSocket sessions

    Args:
        cms_object: CMS object containing request data
        dispatcher: Dispatcher instance for routing and handling
        ws_message: WebSocket message instance from the listener

    Example:
        ```python
        @app.websocket_handler(app.url("ws/notifications"))
        async def notifications(context: WebSocketContext):
            # Get session info
            user_id = context.url_segments.get('user_id')

            # Store session with user mapping
            context.session.user_data['user_id'] = user_id

            # Send to this session
            await context.session.send_json({
                "type": "connected",
                "session_id": context.session.session_id
            })
        ```
    """

    def __init__(self,
                 cms_object: dict,
                 dispatcher: IDispatcher,
                 ws_message: WebSocketMessage) -> None:
        """
        Initialize WebSocket context

        Args:
            cms_object: CMS object containing request data and WebSocket payload
            dispatcher: Dispatcher instance for routing
            ws_message: WebSocket message instance containing session and payload data
        """
        super().__init__(cms_object, dispatcher, True)
        self.message: WebSocketMessage = ws_message
        self.session: WebSocketSession = ws_message.session
        self.session_manager: WebSocketSessionManager = self.session.session_manager

    def __repr__(self) -> str:
        """
        String representation of WebSocketContext for debugging

        Returns:
            str: Human-readable representation with session ID, message type, and URL

        Example:
            ```python
            print(context)
            # Output: WebSocketContext(session_id=a1b2c3d4..., message_type=text, url=/ws/chat)
            ```
        """
        return f"WebSocketContext(session_id={self.session.session_id[:8]}..., message_type={self.message_type}, url={self.url})"
