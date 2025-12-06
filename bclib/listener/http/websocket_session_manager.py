"""WebSocket Session Manager - Centralized management of WebSocket connections

Provides session lifecycle management, group-based messaging, and broadcasting
for WebSocket connections in BasisCore Edge.

Features:
    - Automatic session lifecycle management with weak references
    - Group-based session organization and messaging
    - Broadcast to all sessions or specific groups
    - Heartbeat/ping-pong support for connection health
    - Thread-safe session dictionary with automatic cleanup

Example:
    ```python
    from bclib.websocket import WebSocketSessionManager
    
    # Create manager
    ws_manager = WebSocketSessionManager(
        message_handler=dispatcher,
        heartbeat_interval=30.0
    )
    
    # Handle WebSocket connection (called by HttpListener)
    ws_response = await ws_manager.handle_connection(request, cms_object)
    
    # Group management
    ws_manager.add_to_group(session_id, "chat_room_1")
    await ws_manager.send_to_group("chat_room_1", {"message": "Hello"}, "json")
    
    # Broadcast to all
    await ws_manager.broadcast_to_all("Server announcement", "text")
    ```
"""
import asyncio
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set
from weakref import WeakValueDictionary

from aiohttp import web

from bclib.dispatcher.imessage_handler import IMessageHandler

from .iwebsocket_session_manager import IWebSocketSessionManager
from .websocket_session import WebSocketSession


class WebSocketSessionManager(IWebSocketSessionManager):
    """Manages WebSocket sessions with group support and broadcasting

    Central manager for all WebSocket connections in the application. Handles
    session lifecycle, group-based messaging, and provides weak reference-based
    automatic cleanup when sessions close.

    Attributes:
        _message_handler (IMessageHandler): Message handler for dispatching messages
        _heartbeat_interval (Optional[float]): Ping/pong interval in seconds
        _sessions (Dict[str, WebSocketSession]): Weak-reference session dictionary
        _groups (Dict[str, Set[str]]): Group name to session IDs mapping

    Args:
        message_handler (IMessageHandler): Message handler instance
        heartbeat_interval (Optional[float]): Heartbeat interval (default: 30.0s)

    Example:
        ```python
        # Initialize in dispatcher
        ws_manager = WebSocketSessionManager(
            message_handler=self,
            heartbeat_interval=30.0
        )

        # Access session info
        print(f"Active sessions: {ws_manager.session_count}")
        print(f"Active groups: {ws_manager.group_count}")

        # Get specific session
        session = ws_manager.get_session(session_id)
        if session:
            await session.send_json_async({"status": "ok"})

        # Group operations
        ws_manager.add_to_group(session_id, "admins")
        await ws_manager.send_to_group("admins", "Admin message")
        ```
    """

    def __init__(self,
                 message_handler: IMessageHandler,
                 heartbeat_interval: Optional[float] = 30.0):
        """
        Initialize session manager

        Args:
            message_handler: Message handler instance for dispatching messages
            heartbeat_interval: Interval for ping/pong heartbeat (seconds)
        """
        self._message_handler = message_handler
        self._heartbeat_interval = heartbeat_interval

        # Use WeakValueDictionary for automatic cleanup
        self._sessions: Dict[str, WebSocketSession] = WeakValueDictionary()

        # Group management: group_name -> set of session_ids
        self._groups: Dict[str, Set[str]] = {}

    # ==================== Main Entry Point ====================

    async def handle_connection(self, request: web.Request, cms_object: dict) -> web.WebSocketResponse:
        """Handle WebSocket connection lifecycle from upgrade to close

        Creates WebSocket response, generates session ID, initializes WebSocketSession,
        and manages the full lifecycle until connection closes. Automatically cleans
        up session after completion.

        Args:
            request (web.Request): aiohttp request with WebSocket upgrade
            cms_object (dict): CMS data created by HttpListener

        Returns:
            web.WebSocketResponse: WebSocket response object (after close)

        Notes:
            - Blocks until connection closes
            - Session automatically added to _sessions dictionary
            - Session automatically removed after lifecycle completes
            - Handles cancellation and errors gracefully

        Example:
            ```python
            # Called by HttpListener when WebSocket detected
            cms_object = await WebRequestHelper.create_cms_async(request)
            ws_response = await ws_manager.handle_connection(request, cms_object)
            ```
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
            message_handler=self._message_handler,
            heartbeat_interval=self._heartbeat_interval,
            session_manager=self
        )

        # Register session
        self._sessions[session_id] = session

        # Wait for session lifecycle to complete (blocks until connection closes)
        if session._lifecycle_task:
            try:
                await session._lifecycle_task
            except asyncio.CancelledError as log_ex:
                # Task cancellation is expected during normal shutdown; ignore.
                logging.warning("WebSocket session cancelled: %s", log_ex)
            except Exception as log_ex:
                logging.error(
                    "Error occurred while waiting for WebSocket session to close: %s", log_ex)

        # Clean up session after completion
        self._sessions.pop(session_id, None)

        # Return WebSocket response after connection closes
        return ws

    # ==================== Session Management ====================

    async def remove_session(self, session_id: str) -> None:
        """Remove and cleanup session from manager

        Stops session lifecycle, closes WebSocket connection, and removes
        from session dictionary. Safe to call even if session doesn't exist.

        Args:
            session_id (str): Session identifier

        Notes:
            - Stops lifecycle task if running
            - Closes WebSocket if not already closed
            - Errors during close are logged but not raised
            - No-op if session doesn't exist
        """
        session = self._sessions.pop(session_id, None)
        if session:
            # Stop session lifecycle
            await session.stop_async()

            # Close WebSocket if not already closed
            if not session.closed:
                try:
                    await session.close_async()
                except Exception as log_ex:
                    logging.warning(
                        "Error occurred while closing WebSocket session: %s", log_ex)
                    pass

    def get_session(self, session_id: str) -> Optional[WebSocketSession]:
        """Get active session by ID

        Retrieves WebSocketSession from session dictionary if it exists
        and is still active.

        Args:
            session_id (str): Session identifier

        Returns:
            Optional[WebSocketSession]: Session object or None if not found

        Example:
            ```python
            session = ws_manager.get_session("abc-123")
            if session:
                await session.send_text_async("Hello")
            ```
        """
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> List[WebSocketSession]:
        """Get all active sessions

        Returns snapshot of all currently active WebSocket sessions.

        Returns:
            List[WebSocketSession]: List of active session objects

        Example:
            ```python
            for session in ws_manager.get_active_sessions():
                print(f"Session {session.session_id}: {session.remote_address}")
            ```
        """
        return list(self._sessions.values())

    @property
    def session_count(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)

    # ==================== Group Management ====================

    def add_to_group(self, session_id: str, group_name: str) -> bool:
        """Add session to a named group

        Adds session to group for group-based messaging. Creates group
        if it doesn't exist. Session must exist in manager.

        Args:
            session_id (str): Session identifier
            group_name (str): Group name to join

        Returns:
            bool: True if session exists and was added, False if session not found

        Example:
            ```python
            # Add to chat room
            if ws_manager.add_to_group(session_id, "chat_room_1"):
                await ws_manager.send_to_group(
                    "chat_room_1",
                    {"event": "user_joined"},
                    "json"
                )
            ```
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
        """Remove session from a named group

        Removes session from group. Automatically deletes group if it becomes empty.

        Args:
            session_id (str): Session identifier
            group_name (str): Group name to leave

        Returns:
            bool: True if session was in group and removed, False otherwise

        Example:
            ```python
            if ws_manager.remove_from_group(session_id, "chat_room_1"):
                await ws_manager.send_to_group(
                    "chat_room_1",
                    {"event": "user_left"},
                    "json"
                )
            ```
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
        """Get all sessions in a specific group

        Returns active sessions in group and automatically cleans up
        removed/closed sessions. Deletes group if empty after cleanup.

        Args:
            group_name (str): Group name

        Returns:
            List[WebSocketSession]: List of active sessions in group

        Notes:
            - Automatically filters out closed sessions
            - Cleans up group if all sessions removed
            - Returns empty list if group doesn't exist

        Example:
            ```python
            sessions = ws_manager.get_group_sessions("chat_room_1")
            print(f"Room has {len(sessions)} active users")
            ```
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
        """Get all groups a session belongs to

        Returns list of group names that contain the specified session.

        Args:
            session_id (str): Session identifier

        Returns:
            List[str]: List of group names (empty if session not in any groups)

        Example:
            ```python
            groups = ws_manager.get_session_groups(session_id)
            print(f"User is in groups: {', '.join(groups)}")
            ```
        """
        return [group_name for group_name, session_ids in self._groups.items()
                if session_id in session_ids]

    async def send_to_group(self, group_name: str, message: Any, message_type: str = 'text') -> int:
        """Send message to all sessions in a group

        Sends message to all active sessions in group. Continues on individual
        send failures (e.g., closed connections).

        Args:
            group_name (str): Target group name
            message (Any): Message to send (str for text, dict for json, bytes for binary)
            message_type (str): Message type: 'text', 'json', or 'binary' (default: 'text')

        Returns:
            int: Number of sessions message was successfully sent to

        Example:
            ```python
            # Send JSON to chat room
            sent_count = await ws_manager.send_to_group(
                "chat_room_1",
                {"user": "Alice", "message": "Hello everyone!"},
                "json"
            )
            print(f"Message sent to {sent_count} users")

            # Send text notification
            await ws_manager.send_to_group("admins", "Server maintenance in 5 min")
            ```
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
        """Broadcast message to all active sessions

        Sends message to every active WebSocket session. Continues on individual
        send failures (e.g., closed connections).

        Args:
            message (Any): Message to send (str for text, dict for json, bytes for binary)
            message_type (str): Message type: 'text', 'json', or 'binary' (default: 'text')

        Returns:
            int: Number of sessions message was successfully sent to

        Example:
            ```python
            # Broadcast server announcement
            sent = await ws_manager.broadcast_to_all(
                {"type": "announcement", "text": "Server restarting"},
                "json"
            )
            print(f"Announcement sent to {sent} connected users")

            # Simple text broadcast
            await ws_manager.broadcast_to_all("System maintenance")
            ```
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
