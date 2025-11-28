"""Example: TCP Endpoint Server and Client Communication"""
import asyncio
import json

from bclib import edge
from bclib.context import RESTfulContext

# =============================================================================
# SERVER SIDE
# =============================================================================

# Create dispatcher with endpoint listener
server_options = {
    "endpoint": "127.0.0.1:1025",
}

app = edge.from_options(server_options)


@app.restful_action(app.get("api/hello"))
async def hello_handler(context: RESTfulContext):
    """Handle hello requests"""
    return {
        "message": "Hello from endpoint server!",
        "session": context.cms.request.get("session-id", "unknown")
    }


@app.restful_action(app.get("api/users/:id"))
async def user_handler(context: RESTfulContext):
    """Handle user requests with URL parameter"""
    user_id = context.url_segments.get("id", "unknown")
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "status": "active"
    }


def start_server():
    """Start the endpoint server"""
    print("=" * 70)
    print("TCP Endpoint Server Example")
    print("=" * 70)
    print()
    print("Server: 127.0.0.1:1025")
    print()
    print("Endpoints:")
    print("  api/hello      - Simple hello endpoint")
    print("  api/users/:id  - User details with parameter")
    print()
    print("=" * 70)

    app.listening()


# =============================================================================
# CLIENT SIDE
# =============================================================================

async def send_endpoint_message(host: str, port: int, cms_data: dict):
    """
    Send message to endpoint server and receive response

    Args:
        host: Server hostname/IP
        port: Server port
        cms_data: CMS object containing request data

    Returns:
        Response CMS object
    """
    import uuid

    from bclib.listener import MessageType, TcpMessage

    # Connect to server
    reader, writer = await asyncio.open_connection(host, port)

    try:
        # Create message
        session_id = str(uuid.uuid4())
        payload = json.dumps({"cms": cms_data}).encode("utf-8")

        # Create TcpMessage and write to stream
        message = TcpMessage(
            reader, writer, session_id, MessageType.AD_HOC, payload)
        await message.write_to_stream_async(writer)

        # Read response
        response = await TcpMessage.read_from_stream_async(reader, writer)

        if response and response.buffer:
            response_data = json.loads(response.buffer.decode("utf-8"))
            return response_data

        return None

    finally:
        writer.close()
        await writer.wait_closed()


async def test_client():
    """Test client for endpoint communication"""
    print("\n" + "=" * 70)
    print("Testing Endpoint Client")
    print("=" * 70)

    # Test 1: Simple hello request
    print("\n[Test 1] Sending request to api/hello...")
    cms_data = {
        "request": {
            "url": "api/hello",
            "methode": "get"
        }
    }

    response = await send_endpoint_message("127.0.0.1", 1025, cms_data)
    print(f"Response: {json.dumps(response, indent=2)}")

    # Test 2: User request with parameter
    print("\n[Test 2] Sending request to api/users/123...")
    cms_data = {
        "request": {
            "url": "api/users/123",
            "methode": "get"
        }
    }

    response = await send_endpoint_message("127.0.0.1", 1025, cms_data)
    print(f"Response: {json.dumps(response, indent=2)}")

    print("\n" + "=" * 70)
    print("Client tests completed!")
    print("=" * 70)


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # Run as client
        asyncio.run(test_client())
    else:
        # Run as server
        start_server()
