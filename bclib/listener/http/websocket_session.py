"""WebSocket Session - Individual WebSocket connection lifecycle management

Manages a single active WebSocket connection including message handling, heartbeat,
and lifecycle events (connect, message, disconnect) for BasisCore Edge.

Features:
    - Automatic connection lifecycle management (CONNECT → MESSAGE → DISCONNECT)
    - Heartbeat/ping for connection health monitoring
    - Message type handling (text, binary, close, error)
    - Graceful error handling and cleanup
    - Integration with WebSocketSessionManager for session registry

Example:
    ```python
    # Created automatically by WebSocketSessionManager
    session = WebSocketSession(
        ws=web.WebSocketResponse(),
        cms_object=cms_data,
        request=request,
        session_id=str(uuid.uuid4()),
        message_handler=dispatcher,
        heartbeat_interval=30.0,
        session_manager=ws_manager
    )
    
    # Send messages
    await session.send_text_async("Hello")
    await session.send_json_async({"type": "notification"})
    await session.send_bytes_async(b"binary data")
    
    # Close connection
    await session.close_async(code=1000, message="Normal closure")
    ```
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

from aiohttp import WSMsgType

from bclib.listener.message_type import MessageType

if TYPE_CHECKING:
    from aiohttp import web

    from bclib.dispatcher import IMessageHandler
    from bclib.listener.http.websocket_message import WebSocketMessage
    from bclib.websocket.websocket_session_manager import \
        WebSocketSessionManager


class WebSocketSession:
    """Manages individual WebSocket connection lifecycle and messaging

    Represents a single active WebSocket connection with automatic lifecycle
    management, heartbeat monitoring, and message dispatching to handlers.

    Attributes:
        ws (web.WebSocketResponse): aiohttp WebSocket response object
        session_id (str): Unique session identifier (UUID)
        request (web.Request): Original HTTP request that upgraded to WebSocket
        cms_object (dict): CMS data from initial connection
        url (str): WebSocket URL from CMS request data
        session_manager (Optional[WebSocketSessionManager]): Parent session manager
        _message_handler (IMessageHandler): Message handler instance
        _heartbeat_interval (float): Ping interval in seconds
        _lifecycle_task (Optional[asyncio.Task]): Main lifecycle task

    Args:
        ws (web.WebSocketResponse): WebSocket response from aiohttp
        cms_object (dict): CMS data structure from connection
        request (web.Request): HTTP request object
        session_id (str): Unique identifier for this session
        message_handler (IMessageHandler): Message handler instance
        heartbeat_interval (float): Ping/pong interval (default: 30.0s)
        session_manager (Optional[WebSocketSessionManager]): Manager reference

    Lifecycle:
        1. CONNECT message sent on initialization
        2. MESSAGE events dispatched for each received message
        3. DISCONNECT message sent on close/error
        4. Automatic cleanup and heartbeat cancellation

    Example:
        ```python
        # Typically created by WebSocketSessionManager
        session = WebSocketSession(
            ws=await web.WebSocketResponse().prepare(request),
            cms_object=cms_data,
            request=request,
            session_id="abc-123-def",
            message_handler=dispatcher,
            heartbeat_interval=30.0,
            session_manager=ws_manager
        )

        # Access session properties
        print(f"Session: {session.id}")
        print(f"URL: {session.url}")
        print(f"Closed: {session.closed}")

        # Send messages
        if not session.closed:
            await session.send_json_async({"data": "value"})
        ```
    """

    def __init__(self,
                 ws: 'web.WebSocketResponse',
                 cms_object: dict,
                 request: 'web.Request',
                 session_id: str,
                 message_handler: 'IMessageHandler',
                 heartbeat_interval: float = 30.0,
                 session_manager: Optional['WebSocketSessionManager'] = None):
        """Initialize WebSocket session and start lifecycle

        Creates session and automatically starts lifecycle task that handles
        CONNECT, MESSAGE, and DISCONNECT events.

        Args:
            ws (web.WebSocketResponse): Prepared WebSocket response
            cms_object (dict): CMS data from connection request
            request (web.Request): HTTP upgrade request
            session_id (str): Unique session identifier
            message_handler (IMessageHandler): Message handler instance
            heartbeat_interval (float): Ping interval in seconds (default: 30.0)
            session_manager (Optional[WebSocketSessionManager]): Manager reference
        """
        self.ws = ws
        self.id = session_id
        self.request = request
        self.cms_object = cms_object
        self.url = self.cms_object.get('request', {}).get('url')
        self._message_handler = message_handler
        self._heartbeat_interval = heartbeat_interval
        self.session_manager = session_manager
        self._lifecycle_task: Optional[asyncio.Task] = asyncio.create_task(
            self._start_async())

    @property
    def closed(self) -> bool:
        """Check if WebSocket is closed"""
        return self.ws.closed

    # ==================== Send Methods ====================

    async def send_text_async(self, text: str) -> None:
        """Send text message to client

        Args:
            text (str): Text message to send

        Notes:
            - No-op if WebSocket is closed
            - Safe to call even after close
        """
        if not self.ws.closed:
            await self.ws.send_str(text)

    async def send_json_async(self, obj: Any) -> None:
        """Send JSON message to client

        Args:
            obj (Any): Object to serialize as JSON

        Notes:
            - No-op if WebSocket is closed
            - Object must be JSON-serializable
        """
        if not self.ws.closed:
            await self.ws.send_json(obj)

    async def send_bytes_async(self, data: bytes) -> None:
        """Send binary message to client

        Args:
            data (bytes): Binary data to send

        Notes:
            - No-op if WebSocket is closed
        """
        if not self.ws.closed:
            await self.ws.send_bytes(data)

    async def close_async(self, code: int = 1000, message: str = '') -> None:
        """Close WebSocket connection with optional code and message

        Args:
            code (int): WebSocket close code (default: 1000 = normal closure)
            message (str): Optional close reason (default: empty)

        Notes:
            - No-op if already closed
            - Code 1000 = normal closure
            - Code 1001 = going away
            - See RFC 6455 for other codes
        """
        if not self.ws.closed:
            await self.ws.close(code=code, message=message.encode() if message else b'')

    async def stop_async(self) -> None:
        """Stop session and cancel all tasks

        Cancels lifecycle task and waits for cancellation to complete.
        Should be called before closing WebSocket.

        Notes:
            - Handles CancelledError gracefully
            - Safe to call multiple times
        """
        # Cancel lifecycle task
        if self._lifecycle_task and not self._lifecycle_task.done():
            self._lifecycle_task.cancel()
            try:
                await self._lifecycle_task
            except asyncio.CancelledError:
                # Task cancellation is expected when stopping the session; ignore.
                pass

    # ==================== Connection Lifecycle ====================

    async def _start_async(self) -> None:
        """Main lifecycle loop - handles connection from start to finish (internal)

        Manages complete WebSocket lifecycle:
        1. Sends CONNECT message
        2. Starts heartbeat loop
        3. Receives and dispatches messages (TEXT, BINARY, CLOSE, ERROR)
        4. Handles errors and cancellation
        5. Sends DISCONNECT message
        6. Cleans up heartbeat and closes WebSocket

        Notes:
            - Called automatically on session creation
            - Runs until connection closes or error occurs
            - All exceptions are handled and logged
            - Cleanup always executes in finally block
        """
        from bclib.listener.http.websocket_message import WebSocketMessage

        # Heartbeat task as local variable
        heartbeat_task: Optional[asyncio.Task] = None
        exit_code = None
        try:
            # Send CONNECT message
            connect_msg = WebSocketMessage.connect(self, MessageType.CONNECT)
            await self._message_handler.on_message_receive_async(connect_msg)

            # Start heartbeat
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop()
            )

            # Infinite message receiving loop - continues until connection closes

            while not self.ws.closed:
                try:
                    msg = await self.ws.receive()

                    if msg.type == WSMsgType.TEXT:
                        # Text message
                        ws_msg = WebSocketMessage.text_message(
                            self, MessageType.MESSAGE, msg.data)
                        await self._message_handler.on_message_receive_async(ws_msg)

                    elif msg.type == WSMsgType.BINARY:
                        # Binary message
                        ws_msg = WebSocketMessage.binary_message(
                            self, MessageType.MESSAGE, msg.data)
                        await self._message_handler.on_message_receive_async(ws_msg)

                    elif msg.type == WSMsgType.CLOSE:
                        # Close message
                        exit_code = msg.data

                        # Connection is closing, exit loop
                        break

                    elif msg.type == WSMsgType.ERROR:
                        # Error message
                        ws_msg = WebSocketMessage.error(
                            self, MessageType.MESSAGE, self.ws.exception())
                        await self._message_handler.on_message_receive_async(ws_msg)
                        # Connection has error, exit loop
                        break

                except Exception as recv_ex:
                    # Handle receive errors
                    error_msg = WebSocketMessage.error(
                        self, MessageType.MESSAGE, recv_ex)
                    try:
                        await self._message_handler.on_message_receive_async(error_msg)
                    except Exception as log_ex:
                        # Suppress all exceptions here as the connection may already be broken; best effort to dispatch error message.
                        logging.exception(
                            "Exception while dispatching error message in WebSocketSession: %s", log_ex)
                        pass
                    break

        except asyncio.CancelledError:
            # Task was cancelled - normal cleanup
            pass
        except Exception as log_ex:
            # Handle unexpected errors
            error_msg = WebSocketMessage.error(
                self, MessageType.MESSAGE, log_ex)
            try:
                await self._message_handler.on_message_receive_async(error_msg)
            except Exception as log_ex:
                logging.exception(
                    "Exception occurred while dispatching error message during WebSocketSession._start_async cleanup. %s", log_ex)
                pass  # Best effort
        finally:
            # Send DISCONNECT message
            await self._send_disconnect(exit_code)

            # Cancel heartbeat task
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    # Task was cancelled during cleanup; this is expected and safe to ignore.
                    pass

            # Close WebSocket if not already closed
            if not self.closed:
                try:
                    await self.close_async()
                except Exception as log_ex:
                    logging.exception(
                        "Exception occurred while closing WebSocket during cleanup: %s", log_ex)
                    pass

    async def _heartbeat_loop(self) -> None:
        """Send periodic pings to keep connection alive (internal)

        Continuously sends ping messages at configured interval to detect
        dead connections and keep connection active.

        Notes:
            - Sleeps for _heartbeat_interval between pings
            - Exits gracefully on cancellation
            - Logs errors but continues on failure
            - aiohttp automatically handles pong responses
        """
        try:
            while not self.closed:
                await asyncio.sleep(self._heartbeat_interval)
                if not self.closed:
                    await self.ws.ping()
        except asyncio.CancelledError:
            pass  # Normal cancellation
        except Exception as log_ex:
            logging.exception("Failed to send ping: %s", log_ex)
            pass  # Best effort

    async def _send_disconnect(self, exit_code: int) -> None:
        """Send DISCONNECT message to dispatcher (internal)

        Creates and dispatches DISCONNECT message with exit code to notify
        handlers that connection is closing.

        Args:
            exit_code (int): WebSocket close code (or None)

        Notes:
            - Best effort - logs errors but doesn't raise
            - Called in finally block of lifecycle
        """
        from bclib.listener.http.websocket_message import WebSocketMessage
        disconnect_msg = WebSocketMessage.disconnect(
            self, MessageType.DISCONNECT, code=exit_code)
        try:
            await self._message_handler.on_message_receive_async(disconnect_msg)
        except Exception as log_ex:
            logging.exception(
                "Failed to dispatch disconnect message: %s", log_ex)
            pass  # Best effort

    def __repr__(self) -> str:
        status = "closed" if self.closed else "open"
        return f"WebSocketSession(session_id={self.id[:8]}..., status={status}, url={self.url})"
