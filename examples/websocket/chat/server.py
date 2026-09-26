"""Minimal group-chat WebSocket sample."""
from pathlib import Path

from bclib import edge
from bclib.context import WebSocketContext
from bclib.utility import StaticFileHandler

app = edge.from_options(
    {
        "name": "ws-chat",
        "http": "localhost:9186",
        "log_error": True,
        "log_request": True,
    }
)

app.add_static_handler(
    StaticFileHandler(
        base_dir=Path(__file__).parent,
        enable_index=True,
        index_files=["chat.html"],
    )
)


@app.handler("chat/:room")
async def chat(context: WebSocketContext, room: str):
    session = context.session
    manager = context.session_manager

    if context.message.is_connect:
        manager.try_add_to_group(session.id, room)
        await manager.send_json_to_group_async(
            room,
            {"type": "join", "session": session.id[:8], "room": room},
        )
    elif context.message.is_text:
        await manager.send_json_to_group_async(
            room,
            {
                "type": "message",
                "from": session.id[:8],
                "room": room,
                "text": context.message.text,
            },
        )
    elif context.message.is_disconnect:
        manager.try_remove_from_group(session.id, room)
        await manager.send_json_to_group_async(
            room,
            {"type": "leave", "session": session.id[:8], "room": room},
        )


if __name__ == "__main__":
    print("Chat -> http://localhost:9186/  WS /chat/lobby")
    app.listening()
