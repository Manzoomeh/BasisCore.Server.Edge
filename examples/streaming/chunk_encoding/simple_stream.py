"""Chunked HTML stream over web_handler."""
import asyncio
import json
from pathlib import Path

from bclib import edge
from bclib.context import HttpContext

options = {
    "name": "chunk-stream",
    "http": "localhost:9183",
    "router": "web",
}

app = edge.from_options(options)


@app.web_handler(app.get("stream"))
async def stream_handler(context: HttpContext):
    await context.start_stream_response_async(
        headers={"Content-Type": "text/html; charset=utf-8"}
    )
    for count in range(6):
        await context.write_and_drain_async(json.dumps({"id": count}).encode())
        await asyncio.sleep(0.2)
    return True


@app.web_handler()
def index(_: HttpContext):
    return (Path(__file__).parent / "index.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    print("Chunk stream -> http://localhost:9183/stream")
    app.listening()
