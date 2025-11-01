"""WebSocket Session Manager - manages dictionary of all WebSocket sessions"""
import asyncio
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set
from weakref import WeakValueDictionary

from aiohttp import web

from bclib.dispatcher.websocket_session import WebSocketSession
from bclib.listener.message import Message


class WebSocketSessionManager:
    """Manages dictionary of WebSocket sessions with group support"""

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

        # Group management: group_name -> set of session_ids
        self._groups: Dict[str, Set[str]] = {}

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
            heartbeat_interval=self._heartbeat_interval,
            session_manager=self
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

    # ==================== Group Management ====================

    def add_to_group(self, session_id: str, group_name: str) -> bool:
        """
        Add a session to a group

        Args:
            session_id: Session identifier
            group_name: Group name

        Returns:
            True if session exists and was added to group, False otherwise
        """
        # Check if session exists
        if session_id not in self._sessions:
            return False

        # Create group if it doesn't exist
        if group_name not in self._groups:
            self._groups[group_name] = set()

        # Add session to group
        self._groups[group_name].add(session_id)
        return True

    def remove_from_group(self, session_id: str, group_name: str) -> bool:
        """
        Remove a session from a group

        Args:
            session_id: Session identifier
            group_name: Group name

        Returns:
            True if session was in group and removed, False otherwise
        """
        if group_name not in self._groups:
            return False

        if session_id in self._groups[group_name]:
            self._groups[group_name].discard(session_id)

            # Remove group if empty
            if not self._groups[group_name]:
                del self._groups[group_name]

            return True
        return False

    def get_group_sessions(self, group_name: str) -> List[WebSocketSession]:
        """
        Get all sessions in a specific group

        Args:
            group_name: Group name

        Returns:
            List of WebSocket sessions in the group
        """
        if group_name not in self._groups:
            return []

        # Get sessions that still exist (filter out removed ones)
        sessions = []
        session_ids_to_remove = []

        for session_id in self._groups[group_name]:
            session = self._sessions.get(session_id)
            if session:
                sessions.append(session)
            else:
                # Mark for removal (session no longer exists)
                session_ids_to_remove.append(session_id)

        # Clean up removed sessions from group
        for session_id in session_ids_to_remove:
            self._groups[group_name].discard(session_id)

        # Remove group if empty
        if not self._groups[group_name]:
            del self._groups[group_name]

        return sessions

    def get_session_groups(self, session_id: str) -> List[str]:
        """
        Get all groups a session belongs to

        Args:
            session_id: Session identifier

        Returns:
            List of group names
        """
        return [group_name for group_name, session_ids in self._groups.items()
                if session_id in session_ids]

    async def send_to_group(self, group_name: str, message: Any, message_type: str = 'text') -> int:
        """
        Send a message to all sessions in a group

        Args:
            group_name: Group name
            message: Message to send (text, dict for JSON, or bytes)
            message_type: Type of message ('text', 'json', or 'binary')

        Returns:
            Number of sessions message was sent to
        """
        sessions = self.get_group_sessions(group_name)
        success_count = 0

        for session in sessions:
            try:
                if message_type == 'text':
                    await session.send_text_async(str(message))
                    success_count += 1
                elif message_type == 'json':
                    await session.send_json_async(message)
                    success_count += 1
                elif message_type == 'binary':
                    await session.send_bytes_async(message)
                    success_count += 1
            except Exception:
                # Session might be closed, continue with others
                pass

        return success_count

    async def broadcast_to_all(self, message: Any, message_type: str = 'text') -> int:
        """
        Broadcast a message to all active sessions

        Args:
            message: Message to send (text, dict for JSON, or bytes)
            message_type: Type of message ('text', 'json', or 'binary')

        Returns:
            Number of sessions message was sent to
        """
        sessions = self.get_active_sessions()
        success_count = 0

        for session in sessions:
            try:
                if message_type == 'text':
                    await session.send_text_async(str(message))
                    success_count += 1
                elif message_type == 'json':
                    await session.send_json_async(message)
                    success_count += 1
                elif message_type == 'binary':
                    await session.send_bytes_async(message)
                    success_count += 1
            except Exception:
                # Session might be closed, continue with others
                pass

        return success_count

    @property
    def group_count(self) -> int:
        """Get number of active groups"""
        return len(self._groups)

    def get_all_groups(self) -> List[str]:
        """Get list of all group names"""
        return list(self._groups.keys())

    def __repr__(self) -> str:
        return f"WebSocketSessionManager(active_sessions={self.session_count}, groups={self.group_count})"
