"""WebSocket Session - manages an active WebSocket connection session"""
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from aiohttp import WSMsgType

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType
from bclib.utility import DictEx

if TYPE_CHECKING:
    from aiohttp import web

    from bclib.listener.http_listener.websocket_message import WebSocketMessage
    from bclib.websocket.websocket_session_manager import \
        WebSocketSessionManager


class WebSocketSession:
    """Manages an active WebSocket connection session"""

    def __init__(self,
                 ws: 'web.WebSocketResponse',
                 cms_object: dict,
                 request: 'web.Request',
                 session_id: str,
                 on_message_receive_async: Callable[[Message], Awaitable[None]],
                 heartbeat_interval: float = 30.0,
                 session_manager: Optional['WebSocketSessionManager'] = None):
        self.ws = ws
        self.session_id = session_id
        self.request = request
        self.cms = DictEx(cms_object) if cms_object else DictEx()
        self.url = self.cms.request.url if self.cms and 'request' in self.cms else None
        self._on_message_receive = on_message_receive_async
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
        """Send text message"""
        if not self.ws.closed:
            await self.ws.send_str(text)

    async def send_json_async(self, obj: Any) -> None:
        """Send JSON message"""
        if not self.ws.closed:
            await self.ws.send_json(obj)

    async def send_bytes_async(self, data: bytes) -> None:
        """Send binary message"""
        if not self.ws.closed:
            await self.ws.send_bytes(data)

    async def close_async(self, code: int = 1000, message: str = '') -> None:
        """Close WebSocket connection"""
        if not self.ws.closed:
            await self.ws.close(code=code, message=message.encode() if message else b'')

    async def stop_async(self) -> None:
        """Stop the session and cancel all tasks"""
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
        """Start the connection loop and heartbeat (internal method)"""
        from bclib.listener.http_listener.websocket_message import \
            WebSocketMessage

        # Heartbeat task as local variable
        heartbeat_task: Optional[asyncio.Task] = None

        try:
            # Send CONNECT message
            connect_msg = WebSocketMessage.connect(self, MessageType.CONNECT)
            await self._dispatch_message(connect_msg)

            # Start heartbeat
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop()
            )

            # Infinite message receiving loop - continues until connection closes
            exit_code = None
            while not self.ws.closed:
                try:
                    msg = await self.ws.receive()

                    if msg.type == WSMsgType.TEXT:
                        # Text message
                        ws_msg = WebSocketMessage.text_message(
                            self, MessageType.MESSAGE, msg.data)
                        await self._dispatch_message(ws_msg)

                    elif msg.type == WSMsgType.BINARY:
                        # Binary message
                        ws_msg = WebSocketMessage.binary_message(
                            self, MessageType.MESSAGE, msg.data)
                        await self._dispatch_message(ws_msg)

                    elif msg.type == WSMsgType.PING:
                        # Ping message
                        ws_msg = WebSocketMessage.ping(
                            self, MessageType.MESSAGE)
                        await self._dispatch_message(ws_msg)
                        # aiohttp automatically sends pong

                    elif msg.type == WSMsgType.PONG:
                        # Pong message
                        ws_msg = WebSocketMessage.pong(
                            self, MessageType.MESSAGE)
                        await self._dispatch_message(ws_msg)

                    elif msg.type == WSMsgType.CLOSE:
                        # Close message
                        exit_code = msg.data

                        # Connection is closing, exit loop
                        break

                    elif msg.type == WSMsgType.ERROR:
                        # Error message
                        ws_msg = WebSocketMessage.error(
                            self, MessageType.MESSAGE, self.ws.exception())
                        await self._dispatch_message(ws_msg)
                        # Connection has error, exit loop
                        break

                except Exception as recv_ex:
                    # Handle receive errors
                    error_msg = WebSocketMessage.error(
                        self, MessageType.MESSAGE, recv_ex)
                    try:
                        await self._dispatch_message(error_msg)
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
                await self._dispatch_message(error_msg)
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

    async def _dispatch_message(self, message: 'WebSocketMessage') -> None:
        """
        Dispatch message to handler

        Args:
            message: WebSocketMessage object ready to dispatch
        """
        # Call dispatcher with Message object (message is already WebSocketMessage)
        await self._on_message_receive(message)

    async def _heartbeat_loop(self) -> None:
        """Send periodic pings to keep connection alive"""
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
        """Send DISCONNECT message"""
        from bclib.listener.http_listener.websocket_message import \
            WebSocketMessage
        disconnect_msg = WebSocketMessage.disconnect(
            self, MessageType.DISCONNECT, code=exit_code)
        try:
            await self._dispatch_message(disconnect_msg)
        except Exception as log_ex:
            logging.exception(
                "Failed to dispatch disconnect message: %s", log_ex)
            pass  # Best effort

    def __repr__(self) -> str:
        status = "closed" if self.closed else "open"
        return f"WebSocketSession(session_id={self.session_id[:8]}..., status={status}, url={self.url})"
