import asyncio
import json
import os

from bclib import edge

if "options" not in dir():
    options = {
        "http": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)


@app.web_handler(app.get("stream"))
async def process_web_handler_async(context: edge.HttpContext):
    print("start")
    await context.start_stream_response_async(headers={'Content-Type': 'text/html; charset=utf-8'})
    count = 0
    while count < 6:
        await context.write_and_drain_async(json.dumps({"id": count}).encode())
        count += 1
        print(count)
        await asyncio.sleep(1)

    print("end")
    return True


@app.web_handler()
def process_web_message(_: edge.HttpContext):
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "index.html")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


app.listening()
