"""WebSocket Session Manager - manages dictionary of all WebSocket sessions"""
import asyncio
import uuid
from typing import Awaitable, Callable, Dict, List, Optional
from weakref import WeakValueDictionary

from aiohttp import web

from bclib.listener.message import Message
from bclib.listener.websocket_session import WebSocketSession


class WebSocketSessionManager:
    """Manages dictionary of WebSocket sessions"""

    def __init__(self,
                 on_message_receive_async: Callable[[Message], Awaitable[Message]],
                 heartbeat_interval: Optional[float] = 30.0):
        """
        Initialize session manager

        Args:
            on_message_receive_async: Callback to dispatch messages to (main dispatcher)
            heartbeat_interval: Interval for ping/pong heartbeat (seconds)
        """
        self._on_message_receive = on_message_receive_async
        self._heartbeat_interval = heartbeat_interval

        # Use WeakValueDictionary for automatic cleanup
        self._sessions: Dict[str, WebSocketSession] = WeakValueDictionary()

    # ==================== Main Entry Point ====================

    async def handle_connection(self, request: web.Request, cms_object: dict) -> web.WebSocketResponse:
        """
        Handle a WebSocket connection

        Args:
            request: aiohttp web request with WebSocket upgrade
            cms_object: CMS object created by HttpListener

        Returns:
            WebSocketResponse object (after connection closes)
        """
        # Create WebSocket response
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Create session (lifecycle starts automatically)
        session = WebSocketSession(
            ws=ws,
            cms_object=cms_object,
            request=request,
            session_id=session_id,
            on_message_receive_async=self._on_message_receive,
            heartbeat_interval=self._heartbeat_interval
        )

        # Register session
        self._sessions[session_id] = session

        # Wait for session lifecycle to complete (blocks until connection closes)
        if session._lifecycle_task:
            try:
                await session._lifecycle_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        # Clean up session after completion
        self._sessions.pop(session_id, None)

        # Return WebSocket response after connection closes
        return ws

    # ==================== Session Management ====================

    async def remove_session(self, session_id: str) -> None:
        """
        Remove session from manager

        Args:
            session_id: Session identifier
        """
        session = self._sessions.pop(session_id, None)
        if session:
            # Stop session lifecycle
            await session.stop_async()

            # Close WebSocket if not already closed
            if not session.closed:
                try:
                    await session.close_async()
                except:
                    pass

    def get_session(self, session_id: str) -> Optional[WebSocketSession]:
        """
        Get active session by ID

        Args:
            session_id: Session identifier

        Returns:
            WebSocket context or None if not found
        """
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> List[WebSocketSession]:
        """
        Get all active sessions

        Returns:
            List of active WebSocket contexts
        """
        return list(self._sessions.values())

    @property
    def session_count(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)

    def __repr__(self) -> str:
        return f"WebSocketSessionManager(active_sessions={self.session_count})"
