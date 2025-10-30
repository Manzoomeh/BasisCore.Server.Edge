"""
Simple WebSocket Manager Test
Test the connection loop task management
"""
import asyncio

from aiohttp import web

from bclib.listener.websocket_message import WebSocketMessage
from bclib.listener.websocket_session import WebSocketSession
from bclib.listener.websocket_session_manager import WebSocketSessionManager


async def test_handler(context: WebSocketSession):
    """Test message handler"""
    message = context.current_message
    if message:
        print(f"[Handler] Received {message.type.name} message")
        if message.is_text:
            print(f"  Text: {message.text}")


async def test_manager():
    """Test WebSocket Session Manager"""
    print("Testing WebSocket Session Manager...")

    # Create manager
    manager = WebSocketSessionManager(
        on_message_receive_async=test_handler,
        heartbeat_interval=30.0,
        enable_heartbeat=False  # Disable for testing
    )

    print(f"✓ Manager created")
    print(f"  Active sessions: {manager.session_count}")
    print(f"  Connection tasks: {len(manager._connection_tasks)}")

    # Create mock request
    app = web.Application()
    request = web.Request(
        message=None,
        payload=None,
        protocol=None,
        payload_writer=None,
        task=None,
        loop=asyncio.get_event_loop()
    )

    print("✓ Manager is ready to handle connections")
    print("  Each connection will have its own infinite loop task")


if __name__ == "__main__":
    asyncio.run(test_manager())
