"""WebSocket Session - manages an active WebSocket connection session"""
import asyncio
import json
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from aiohttp import WSMsgType

from bclib.listener.message import Message
from bclib.utility import DictEx

if TYPE_CHECKING:
    from aiohttp import web

    from bclib.listener.websocket_message import WebSocketMessage, WSMsg


class WebSocketSession:
    """Manages an active WebSocket connection session"""

    def __init__(self,
                 ws: 'web.WebSocketResponse',
                 cms_object: dict,
                 request: 'web.Request',
                 session_id: str,
                 on_message_receive_async: Callable[[Message], Awaitable[Message]],
                 heartbeat_interval: float = 30.0):
        self.ws = ws
        self.session_id = session_id
        self.request = request
        self._cms_container = DictEx(cms_object) if cms_object else DictEx()
        self.cms = DictEx(
            self._cms_container.cms) if 'cms' in self._cms_container else DictEx()
        self.url = self.cms.request.url if self.cms and 'request' in self.cms else None
        self._current_message: Optional['WebSocketMessage'] = None
        self._on_message_receive = on_message_receive_async
        self._heartbeat_interval = heartbeat_interval
        self._lifecycle_task: Optional[asyncio.Task] = None

        # Start lifecycle automatically
        self._lifecycle_task = asyncio.create_task(self._start_async())

    def _set_current_message(self, message: Optional['WebSocketMessage']) -> None:
        """Internal: set current message being processed"""
        self._current_message = message

    @property
    def current_message(self) -> Optional['WebSocketMessage']:
        """Get the current message being processed"""
        return self._current_message

    @property
    def closed(self) -> bool:
        """Check if WebSocket is closed"""
        return self.ws.closed

    @property
    def cms_object(self) -> dict:
        """Get the full CMS container object"""
        return self._cms_container._data if hasattr(self._cms_container, '_data') else dict(self._cms_container)

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
                pass

    # ==================== Request Info ====================

    @property
    def headers(self) -> DictEx:
        """Get request headers"""
        if self.cms and 'request' in self.cms:
            return DictEx(self.cms.request)
        return DictEx()

    @property
    def query(self) -> DictEx:
        """Get query parameters"""
        if self._cms_container and 'query' in self._cms_container:
            return DictEx(self._cms_container.query)
        return DictEx()

    # ==================== Connection Lifecycle ====================

    async def _start_async(self) -> None:
        """Start the connection loop and heartbeat (internal method)"""
        from bclib.listener.websocket_message import WSMsg

        # Heartbeat task as local variable
        heartbeat_task: Optional[asyncio.Task] = None

        try:
            # Send CONNECT message
            connect_msg = WSMsg.connect()
            await self._dispatch_message(connect_msg)

            # Start heartbeat
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop()
            )

            # Infinite message receiving loop
            async for msg in self.ws:
                if msg.type == WSMsgType.TEXT:
                    # Text message
                    ws_msg = WSMsg.text(msg.data)
                    await self._dispatch_message(ws_msg)

                elif msg.type == WSMsgType.BINARY:
                    # Binary message
                    ws_msg = WSMsg.binary(msg.data)
                    await self._dispatch_message(ws_msg)

                elif msg.type == WSMsgType.PING:
                    # Ping message
                    ws_msg = WSMsg.ping()
                    await self._dispatch_message(ws_msg)
                    # aiohttp automatically sends pong

                elif msg.type == WSMsgType.PONG:
                    # Pong message
                    ws_msg = WSMsg.pong()
                    await self._dispatch_message(ws_msg)

                elif msg.type == WSMsgType.CLOSE:
                    # Close message
                    ws_msg = WSMsg.close(
                        code=msg.data if msg.data else 1000)
                    await self._dispatch_message(ws_msg)
                    break

                elif msg.type == WSMsgType.ERROR:
                    # Error message
                    ws_msg = WSMsg.error(self.ws.exception())
                    await self._dispatch_message(ws_msg)
                    break

        except asyncio.CancelledError:
            # Task was cancelled - normal cleanup
            pass
        except Exception as ex:
            # Handle unexpected errors
            from bclib.listener.websocket_message import WSMsg
            error_msg = WSMsg.error(ex)
            try:
                await self._dispatch_message(error_msg)
            except:
                pass  # Best effort
        finally:
            # Cancel heartbeat task
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Send DISCONNECT message
            await self._send_disconnect()

            # Close WebSocket if not already closed
            if not self.closed:
                try:
                    await self.close_async()
                except:
                    pass

    async def _dispatch_message(self, message: 'WSMsg') -> None:
        """
        Dispatch message to handler

        Args:
            message: WebSocket message (internal data structure)
        """
        from bclib.listener.websocket_message import WebSocketMessage

        # Set current message on context
        self._set_current_message(message)

        try:
            # Update CMS container with WebSocket-specific data
            websocket_data = {
                'session_id': self.session_id,
                'message_type': message.type.name,
                'closed': self.closed
            }

            # Add message data
            if message.is_text:
                websocket_data['text'] = message.text
            elif message.is_binary:
                websocket_data['data'] = message.data
            elif message.is_close:
                websocket_data['code'] = message.code
            elif message.is_error:
                websocket_data['error'] = str(message.exception)

            # Update the session's cms_container with websocket data
            self._cms_container['websocket'] = websocket_data

            # Create WebSocketMessage (inherits from Message)
            ws_msg = WebSocketMessage.create_from_websocket(
                session_id=self.session_id,
                session=self,
                ws_message=message
            )

            # Call dispatcher with Message object
            await self._on_message_receive(ws_msg)
        finally:
            # Clear current message
            self._set_current_message(None)

    async def _heartbeat_loop(self) -> None:
        """Send periodic pings to keep connection alive"""
        try:
            while not self.closed:
                await asyncio.sleep(self._heartbeat_interval)
                if not self.closed:
                    await self.ws.ping()
        except asyncio.CancelledError:
            pass  # Normal cancellation
        except Exception:
            pass  # Best effort

    async def _send_disconnect(self) -> None:
        """Send DISCONNECT message"""
        from bclib.listener.websocket_message import WSMsg
        disconnect_msg = WSMsg.disconnect()
        try:
            await self._dispatch_message(disconnect_msg)
        except:
            pass  # Best effort

    def __repr__(self) -> str:
        status = "closed" if self.closed else "open"
        return f"WebSocketSession(session_id={self.session_id[:8]}..., status={status}, url={self.url})"
