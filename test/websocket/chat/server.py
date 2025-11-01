"""Simple WebSocket Chat Server - Group Chat Example"""
import os
import sys

from bclib import edge
from bclib.context import WebSocketContext

# Add parent directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../..')))


async def websocket_handler(context: WebSocketContext):
    """Handle WebSocket chat messages"""
    # Get session and manager from context
    session = context.session
    session_id = session.session_id
    manager = context.session_manager
    print(
        f"[SESSION] Session ID: {session_id[:8]} (messageType={context.message.type.name})")
    if context.message.is_connect:
        # Connection established
        print(f"[CONNECT] Session {session_id[:8]} connected")
        await session.send_json_async({
            "type": "system",
            "message": "Welcome to chat! Use /join <room> to join a room, /leave to leave, /list to see rooms."
        })

    elif context.message.is_disconnect:
        # Connection closed
        print(f"[DISCONNECT] Session {session_id[:8]} disconnected")
        # Remove from all groups
        if manager:
            groups = manager.get_session_groups(session_id)
            for group in groups:
                manager.remove_from_group(session_id, group)
                await notify_room(manager, group, f"User left the room", "system")

    elif context.message.is_text:
        # Text message received
        text = context.message.text
        print(f"[MESSAGE] Session {session_id[:8]}: {text}")

        # Handle commands
        if text.startswith('/'):
            await handle_command(manager, session, text)
        else:
            # Send message to all rooms this session belongs to
            if manager:
                groups = manager.get_session_groups(session_id)
                if groups:
                    for group in groups:
                        await manager.send_to_group(group, {
                            "type": "message",
                            "room": group,
                            "sender": session_id[:8],
                            "message": text
                        }, "json")
                else:
                    await session.send_json_async({
                        "type": "error",
                        "message": "You are not in any room. Use /join <room> to join a room."
                    })

    elif context.message.is_close:
        # Close message received
        print(
            f"[CLOSE] Session {session_id[:8]} closing (code: {context.message.code})")


async def handle_command(manager, session, command_text: str):
    """Handle chat commands"""
    if not manager:
        await session.send_json_async({"type": "error", "message": "Session manager not available"})
        return

    parts = command_text.split(' ', 1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    session_id = session.session_id

    if cmd == '/join':
        if not arg:
            await session.send_json_async({"type": "error", "message": "Usage: /join <room_name>"})
            return

        room_name = arg.strip()
        manager.add_to_group(session_id, room_name)

        await session.send_json_async({
            "type": "system",
            "message": f"Joined room: {room_name}"
        })

        # Notify others in the room
        await notify_room(manager, room_name, f"User {session_id[:8]} joined the room", "system", exclude_session=session_id)

    elif cmd == '/leave':
        groups = manager.get_session_groups(session_id)
        if not groups:
            await session.send_json_async({"type": "error", "message": "You are not in any room"})
            return

        for group in groups:
            manager.remove_from_group(session_id, group)
            await notify_room(manager, group, f"User {session_id[:8]} left the room", "system")

        await session.send_json_async({
            "type": "system",
            "message": f"Left all rooms"
        })

    elif cmd == '/list':
        all_groups = manager.get_all_groups()
        my_groups = manager.get_session_groups(session_id)

        await session.send_json_async({
            "type": "system",
            "message": f"All rooms: {', '.join(all_groups) if all_groups else 'None'}",
            "data": {
                "all_rooms": all_groups,
                "my_rooms": my_groups
            }
        })

    elif cmd == '/rooms':
        my_groups = manager.get_session_groups(session_id)
        await session.send_json_async({
            "type": "system",
            "message": f"Your rooms: {', '.join(my_groups) if my_groups else 'None'}"
        })

    elif cmd == '/help':
        await session.send_json_async({
            "type": "system",
            "message": """Available commands:
/join <room>  - Join a chat room
/leave        - Leave all rooms
/list         - List all rooms
/rooms        - List your rooms
/help         - Show this help"""
        })

    else:
        await session.send_json_async({
            "type": "error",
            "message": f"Unknown command: {cmd}. Type /help for available commands."
        })


async def notify_room(manager, room_name: str, message: str, msg_type: str = "system", exclude_session: str = None):
    """Send notification to all users in a room"""
    if not manager:
        return

    sessions = manager.get_group_sessions(room_name)

    for session in sessions:
        if exclude_session and session.session_id == exclude_session:
            continue

        try:
            await session.send_json_async({
                "type": msg_type,
                "room": room_name,
                "message": message
            })
        except:
            pass


# ==================== Edge Configuration ====================

app = edge.from_options({
    "server":  "localhost:8080",
    "router": {
        "web": ["*"]
    },
    "log_error": True,
    "log_request": True,
})


def readAsset(asset_name: str) -> str:
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), asset_name)
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


@app.web_action()
def default_handler(context: edge.WebContext):
    return readAsset("chat.html")


# Register WebSocket handler
app.websocket_action()(websocket_handler)

# Run the server

print("=" * 60)
print("WebSocket Chat Server Started")
print("=" * 60)
print("Server: ws://localhost:8080")
print("")
print("Commands:")
print("  /join <room>  - Join a chat room")
print("  /leave        - Leave all rooms")
print("  /list         - List all rooms")
print("  /rooms        - List your rooms")
print("  /help         - Show help")
print("=" * 60)
app.listening()
