"""Test streaming response in practice"""
import asyncio

from bclib import edge
from bclib.context import RESTfulContext

# Create dispatcher
options = {
    "server": "localhost:8097",
    "router": "restful",  # Add router configuration
    "log_error": True
}

app = edge.from_options(options)


@app.restful_action(app.get("api/stream"))
async def stream_handler(context: RESTfulContext):
    """Handler that uses streaming response"""

    # Start streaming
    await context.start_stream_response_async(
        status=200,
        headers={'Content-Type': 'text/plain; charset=utf-8'}
    )

    # Write chunks
    for i in range(5):
        chunk = f"Chunk {i + 1}\n".encode('utf-8')
        await context.write_async(chunk)
        await context.drain_async()
        await asyncio.sleep(0.3)

    # No need to return anything - streaming already handled
    return None


@app.restful_action(app.get("api/normal"))
async def normal_handler(context: RESTfulContext):
    """Normal JSON response"""
    return {"message": "Normal response", "streaming": False}


if __name__ == "__main__":
    print("=" * 70)
    print("Streaming Response Test Server")
    print("=" * 70)
    print()
    print("Server: http://localhost:8097")
    print()
    print("Endpoints:")
    print("  GET /stream  - Streaming response (5 chunks with delay)")
    print("  GET /normal  - Normal JSON response")
    print()
    print("Test commands:")
    print("  Invoke-WebRequest http://localhost:8097/stream")
    print("  Invoke-WebRequest http://localhost:8097/normal")
    print()
    print("=" * 70)
    print()

    app.listening()
