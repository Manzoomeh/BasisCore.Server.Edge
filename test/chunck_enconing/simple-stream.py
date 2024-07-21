import asyncio
import os
import json
from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)



@app.web_action(app.get("stream"))
async def process_web_action_async(context: edge.WebContext):
    print("start")
    await context.start_stream_response_async( headers={'Content-Type': 'text/html; charset=utf-8'})
    count = 0
    while count<6:
        await context.write_and_drain_async( json.dumps({"id":count}).encode())
        count+=1
        print(count)
        await asyncio.sleep(1)

    print("end")
    return True

@app.web_action()
def process_web_message(_: edge.WebContext):
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "index.html")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

app.listening()
