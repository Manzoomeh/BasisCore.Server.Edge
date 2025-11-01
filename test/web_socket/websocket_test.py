"""
WebSocket Test - Echo Server Example

This test demonstrates how to use WebSocket support with:
- Session management
- Message handling with decorator
- Different message types (TEXT, BINARY, CONNECT, DISCONNECT)
"""
import asyncio

from bclib.listener import WebSocketSession
from bclib.edge import from_options
from bclib.listener import WebSocketMessage, WSMessageType
from bclib.predicate import Predicate


# Simple echo handler
def ws_echo_handler(context: WebSocketSession, message: WebSocketMessage):
    """
    Echo handler - receives messages and echoes them back

    Args:
        context: WebSocket context
        message: WebSocket message
    """
    print(f"[{context.session_id[:8]}...] Received message type: {message.type.name}")

    if message.is_connect:
        print(f"[{context.session_id[:8]}...] Client connected from {context.url}")
        # Send welcome message
        asyncio.create_task(
            context.send_json_async({
                "type": "welcome",
                "session_id": context.session_id,
                "message": "Connected to echo server"
            })
        )

    elif message.is_text:
        print(f"[{context.session_id[:8]}...] Text message: {message.text}")
        # Echo back
        asyncio.create_task(context.send_text_async(f"Echo: {message.text}"))

    elif message.is_binary:
        print(
            f"[{context.session_id[:8]}...] Binary message: {len(message.data)} bytes")
        # Echo back
        asyncio.create_task(context.send_bytes_async(message.data))

    elif message.is_disconnect:
        print(f"[{context.session_id[:8]}...] Client disconnected")

    elif message.is_close:
        print(
            f"[{context.session_id[:8]}...] Client closed with code: {message.code}")

    elif message.is_error:
        print(f"[{context.session_id[:8]}...] Error: {message.exception}")


# Test with dispatcher decorator
class WebSocketTestDispatcher:
    """Example dispatcher with WebSocket support"""

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.setup_routes()

    def setup_routes(self):
        """Register WebSocket routes"""

        # Echo endpoint - matches /ws/echo
        @self.dispatcher.websocket_action(
            Predicate().add("cms.request.url", "ws/echo")
        )
        async def echo_handler(context: WebSocketSession, message: WebSocketMessage):
            """WebSocket echo handler"""
            if message.is_connect:
                await context.send_json_async({
                    "type": "welcome",
                    "message": "Connected to echo server",
                    "session_id": context.session_id
                })
                print(f"✓ Client connected: {context.session_id[:8]}...")

            elif message.is_text:
                print(f"→ Received: {message.text}")
                await context.send_text_async(f"Echo: {message.text}")

            elif message.is_binary:
                print(f"→ Received binary: {len(message.data)} bytes")
                await context.send_bytes_async(message.data)

            elif message.is_disconnect:
                print(f"✗ Client disconnected: {context.session_id[:8]}...")

        # Chat endpoint - matches /ws/chat
        @self.dispatcher.websocket_action(
            Predicate().add("cms.request.url", "ws/chat")
        )
        async def chat_handler(context: WebSocketSession, message: WebSocketMessage):
            """WebSocket chat handler"""
            if message.is_connect:
                await context.send_json_async({
                    "type": "system",
                    "message": "Welcome to chat room"
                })

            elif message.is_text:
                # Broadcast to all sessions (simple example)
                await context.send_json_async({
                    "type": "message",
                    "sender": context.session_id[:8],
                    "text": message.text
                })


def test_websocket_server():
    """
    Start WebSocket test server

    To test:
    1. Run this script
    2. Connect with WebSocket client to ws://localhost:5000/ws/echo
    3. Send text messages - they will be echoed back

    Example using JavaScript:
        const ws = new WebSocket('ws://localhost:5000/ws/echo');
        ws.onmessage = (event) => console.log('Received:', event.data);
        ws.send('Hello WebSocket!');
    """
    options = {
        "router": {
            "http": [
                {
                    "route": "/",
                    "host": "localhost",
                    "port": 5000
                }
            ]
        }
    }

    # Create dispatcher
    dispatcher = from_options(options)

    # Register WebSocket handlers
    WebSocketTestDispatcher(dispatcher)

    print("=" * 60)
    print("WebSocket Echo Server Started")
    print("=" * 60)
    print("Endpoints:")
    print("  - ws://localhost:5000/ws/echo  (Echo server)")
    print("  - ws://localhost:5000/ws/chat  (Chat room)")
    print("\nTest with WebSocket client:")
    print("  JavaScript: const ws = new WebSocket('ws://localhost:5000/ws/echo');")
    print("  Python: import websocket; ws = websocket.create_connection('ws://localhost:5000/ws/echo')")
    print("=" * 60)

    # Keep running
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    test_websocket_server()
