"""REST streaming response demo."""
import asyncio

from bclib import edge
from bclib.context import RESTfulContext

options = {
    "name": "rest-stream",
    "http": "localhost:9184",
    "router": "restful",
    "log_error": True,
}

app = edge.from_options(options)


@app.restful_handler(app.get("api/stream"))
async def stream_handler(context: RESTfulContext):
    await context.start_stream_response_async(
        status=200,
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    for i in range(5):
        await context.write_async(f"Chunk {i + 1}\n".encode("utf-8"))
        await context.drain_async()
        await asyncio.sleep(0.2)
    return None


@app.restful_handler(app.get("api/normal"))
async def normal_handler(_: RESTfulContext):
    return {"message": "Normal response", "streaming": False}


if __name__ == "__main__":
    print("REST stream -> http://localhost:9184/api/stream")
    app.listening()
