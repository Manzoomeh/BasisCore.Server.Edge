"""WebSocket echo — uses session.id and send_*_async APIs."""
import json
from pathlib import Path

from bclib import edge
from bclib.context import WebSocketContext
from bclib.utility import StaticFileHandler

options = {
    "name": "ws-simple",
    "http": "localhost:9185",
    "log_request": True,
    "log_error": True,
}

app = edge.from_options(options)
app.add_static_handler(
    StaticFileHandler(
        base_dir=Path(__file__).parent,
        enable_index=True,
        index_files=["test.html"],
    )
)


@app.handler("chat/:rkey")
async def handle_websocket(context: WebSocketContext, rkey: str):
    session = context.session
    if context.message.is_connect:
        await session.send_json_async(
            {
                "type": "welcome",
                "message": "Connected",
                "rkey": rkey,
                "session_id": session.id,
            }
        )
    elif context.message.is_text:
        text = context.message.text
        try:
            data = json.loads(text)
            await session.send_json_async(
                {"type": "echo", "original": data, "processed": True}
            )
        except json.JSONDecodeError:
            await session.send_text_async(f"echo: {text}")
    elif context.message.is_disconnect:
        print("client disconnected", session.id[:8])


if __name__ == "__main__":
    print("WebSocket -> http://localhost:9185/  WS path /chat/room1")
    app.listening()
