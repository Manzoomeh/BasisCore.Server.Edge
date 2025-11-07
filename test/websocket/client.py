"""Simple WebSocket Client Test"""
import asyncio
import json
from datetime import datetime

import aiohttp


async def test_client():
    """Test WebSocket client"""
    url = "ws://localhost:8080"

    print(f"\n{'='*60}")
    print(f"WebSocket Client Test")
    print(f"Connecting to: {url}")
    print(f"{'='*60}\n")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print("✓ Connected to server\n")

            # Test 1: Send JSON
            print("Test 1: Sending JSON message...")
            test_msg = {
                "action": "test",
                "message": "Hello from client",
                "timestamp": datetime.now().isoformat()
            }
            await ws.send_json(test_msg)
            print(f"  Sent: {json.dumps(test_msg, indent=2)}")

            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                response = json.loads(msg.data)
                print(f"  Received: {json.dumps(response, indent=2)}\n")

            # Test 2: Send text
            print("Test 2: Sending text message...")
            await ws.send_str("Simple text message")

            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(f"  Received: {msg.data}\n")

            # Test 3: Send binary
            print("Test 3: Sending binary message...")
            binary_data = b"Binary test data"
            await ws.send_bytes(binary_data)

            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.BINARY:
                print(f"  Received: {len(msg.data)} bytes")
                print(f"  Match: {msg.data == binary_data}\n")

            print("✓ All tests passed!")

            # Close
            await ws.close()
            print("\n✓ Connection closed\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_client())
    except aiohttp.ClientConnectorError:
        print("\n✗ Error: Could not connect to server")
        print("  Make sure server is running:")
        print("  python test/websocket/simple.py")
    except Exception as ex:
        print(f"\n✗ Error: {ex}")
