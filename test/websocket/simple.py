import json
from pathlib import Path

from bclib import edge

options = {
    "http": "localhost:8080",
    "log_request": True,
    "log_error": True
}

static_handler = edge.StaticFileHandler(
    base_dir=Path(__file__).parent,
    enable_index=True,
    index_files=['test.html']
)
app = edge.from_options(options)
app.add_static_handler(static_handler)


@app.handler('chat/:rkey')
async def handle_websocket(context: edge.WebSocketContext, rkey: str):
    """Handle WebSocket messages"""
    print(
        f"[SESSION] Session ID: {context.session.session_id[:8]} (messageType={context.message.type.name}, rkey={rkey})")
    # Connection established
    if context.message.is_connect:
        print(
            f"✓ Client connected - Session: {context.session.session_id[:8]}...")
        await context.session.send_json_async({
            "type": "welcome",
            "message": "Connected to WebSocket server!",
            "session_id": context.session.session_id
        })

    # Text message received
    elif context.message.is_text:
        text = context.message.text
        print(f"✓ Received text: {text}")

        try:
            # Try to parse as JSON
            data = json.loads(text)
            print(f"  Parsed JSON: {data}")

            # Echo back with response
            response = {
                "type": "echo",
                "original": data,
                "processed": True
            }
            await context.session.send_json_async(response)
        except json.JSONDecodeError:
            # Just echo text back
            await context.session.send_text_async(f"Echo: {text}")

    # Binary message received
    elif context.message.is_binary:
        data = context.message.binary
        print(f"✓ Received binary: {len(data)} bytes")
        await context.session.send_bytes_async(data)  # Echo back

    # Connection closed
    elif context.message.is_disconnect:
        print(
            f"✓ Client disconnected - Session: {context.session.session_id[:8]}...")

    # Close message
    elif context.message.is_close:
        print(f"✓ Close message received")

    # Error
    elif context.message.is_error:
        print(f"✗ Error occurred")
    return True


print("WebSocket server starting on ws://localhost:8080")
print("Test with:")
print("  - Browser: Open test.html")
print("  - Python: python test/websocket/client.py")
print("-" * 60)

app.listening()
