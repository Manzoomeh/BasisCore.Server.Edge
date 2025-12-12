"""IWebSocketSessionManager - Interface for WebSocket session management

Abstract interface for managing WebSocket connections, sessions, groups, and broadcasting.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from aiohttp import web

    from bclib.listener.http.websocket_session import WebSocketSession


class IWebSocketSessionManager(ABC):
    """Interface for WebSocket session management

    Defines contract for managing WebSocket sessions including lifecycle,
    group-based messaging, and broadcasting capabilities.
    """

    # ==================== Main Entry Point ====================

    @abstractmethod
    async def handle_connection(self, request: 'web.Request', cms_object: dict) -> 'web.WebSocketResponse':
        """Handle WebSocket connection lifecycle from upgrade to close

        Args:
            request (web.Request): aiohttp request with WebSocket upgrade
            cms_object (dict): CMS data created by HttpListener

        Returns:
            web.WebSocketResponse: WebSocket response object (after close)
        """
        pass

    # ==================== Session Management ====================

    @abstractmethod
    async def remove_session(self, session_id: str) -> None:
        """Remove and cleanup session from manager

        Args:
            session_id (str): Session identifier
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> 'Optional[WebSocketSession]':
        """Get active session by ID

        Args:
            session_id (str): Session identifier

        Returns:
            Optional[WebSocketSession]: Session object or None if not found
        """
        pass

    @abstractmethod
    def get_active_sessions(self) -> 'List[WebSocketSession]':
        """Get all active sessions

        Returns:
            List[WebSocketSession]: List of active session objects
        """
        pass

    @property
    @abstractmethod
    def session_count(self) -> int:
        """Get number of active sessions"""
        pass

    # ==================== Group Management ====================

    @abstractmethod
    def try_add_to_group(self, session_id: str, group_name: str) -> bool:
        """Add session to a named group

        Args:
            session_id (str): Session identifier
            group_name (str): Group name to join

        Returns:
            bool: True if session exists and was added, False if session not found
        """
        pass

    @abstractmethod
    def try_remove_from_group(self, session_id: str, group_name: str) -> bool:
        """Remove session from a named group

        Args:
            session_id (str): Session identifier
            group_name (str): Group name to leave

        Returns:
            bool: True if session was in group and removed, False otherwise
        """
        pass

    @abstractmethod
    def get_group_sessions(self, group_name: str) -> 'List[WebSocketSession]':
        """Get all sessions in a specific group

        Args:
            group_name (str): Group name

        Returns:
            List[WebSocketSession]: List of active sessions in group
        """
        pass

    @abstractmethod
    def get_session_groups(self, session_id: str) -> List[str]:
        """Get all groups a session belongs to

        Args:
            session_id (str): Session identifier

        Returns:
            List[str]: List of group names (empty if session not in any groups)
        """
        pass

    @abstractmethod
    async def send_text_to_group_async(self, group_name: str, message: str) -> int:
        """Send text message to all sessions in a group

        Args:
            group_name (str): Target group name
            message (str): Text message to send

        Returns:
            int: Number of sessions message was successfully sent to
        """
        pass

    @abstractmethod
    async def send_json_to_group_async(self, group_name: str, message: Any) -> int:
        """Send JSON message to all sessions in a group

        Args:
            group_name (str): Target group name
            message (Any): Object to serialize as JSON

        Returns:
            int: Number of sessions message was successfully sent to
        """
        pass

    @abstractmethod
    async def send_bytes_to_group_async(self, group_name: str, message: bytes) -> int:
        """Send binary message to all sessions in a group

        Args:
            group_name (str): Target group name
            message (bytes): Binary data to send

        Returns:
            int: Number of sessions message was successfully sent to
        """
        pass

    @abstractmethod
    async def broadcast_text_to_all_async(self, message: str) -> int:
        """Broadcast text message to all active sessions

        Args:
            message (str): Text message to send

        Returns:
            int: Number of sessions message was successfully sent to
        """
        pass

    @abstractmethod
    async def broadcast_json_to_all_async(self, message: Any) -> int:
        """Broadcast JSON message to all active sessions

        Args:
            message (Any): Object to serialize as JSON

        Returns:
            int: Number of sessions message was successfully sent to
        """
        pass

    @abstractmethod
    async def broadcast_bytes_to_all_async(self, message: bytes) -> int:
        """Broadcast binary message to all active sessions

        Args:
            message (bytes): Binary data to send

        Returns:
            int: Number of sessions message was successfully sent to
        """
        pass

    @property
    @abstractmethod
    def group_count(self) -> int:
        """Get number of active groups"""
        pass

    @abstractmethod
    def get_all_groups(self) -> List[str]:
        """Get list of all group names"""
        pass
