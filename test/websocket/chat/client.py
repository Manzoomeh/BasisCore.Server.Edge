"""Simple WebSocket Chat Client - Console Client"""
import asyncio
import json
import sys

import aiohttp


async def chat_client(username: str = None):
    """Simple console chat client"""
    url = "ws://localhost:8080"

    if not username:
        username = input("Enter your username: ").strip() or "Anonymous"

    print(f"\n{'='*60}")
    print(f"Connecting to chat server as: {username}")
    print(f"{'='*60}\n")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print(f"✓ Connected to {url}")
            print("Type your messages or use commands (/help for list)\n")

            # Task for receiving messages
            async def receive_messages():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            msg_type = data.get('type', 'unknown')

                            if msg_type == 'system':
                                print(f"\n[SYSTEM] {data.get('message', '')}")
                            elif msg_type == 'message':
                                room = data.get('room', '')
                                sender = data.get('sender', 'Unknown')
                                message = data.get('message', '')
                                print(f"\n[{room}] {sender}: {message}")
                            elif msg_type == 'error':
                                print(f"\n[ERROR] {data.get('message', '')}")
                            else:
                                print(f"\n[{msg_type.upper()}] {data}")

                            # Re-print prompt
                            print(f"\n[{username}] ", end='', flush=True)
                        except json.JSONDecodeError:
                            print(f"\n[RAW] {msg.data}")

                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("\n✗ Connection closed by server")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"\n✗ WebSocket error: {ws.exception()}")
                        break

            # Task for sending messages
            async def send_messages():
                loop = asyncio.get_event_loop()
                while True:
                    try:
                        # Read from console
                        message = await loop.run_in_executor(None, input, f"[{username}] ")

                        if message.strip():
                            if message.strip().lower() in ['/quit', '/exit', '/q']:
                                print("Disconnecting...")
                                await ws.close()
                                break
                            else:
                                await ws.send_str(message)
                    except EOFError:
                        break
                    except Exception as e:
                        print(f"\n✗ Error sending message: {e}")
                        break

            # Run both tasks concurrently
            receive_task = asyncio.create_task(receive_messages())
            send_task = asyncio.create_task(send_messages())

            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            print("\n✓ Disconnected from chat server")


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        asyncio.run(chat_client(username))
    except KeyboardInterrupt:
        print("\n\n✓ Chat client stopped")
    except Exception as e:
        print(f"\n✗ Error: {e}")
