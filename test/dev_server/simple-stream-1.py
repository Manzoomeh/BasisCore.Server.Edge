import asyncio
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
    await context.write_and_drain_async(b"start of data<br/>")
    count = 0
    while count<6:
        await context.write_and_drain_async("data is {0}...<br/>".format(count).encode())
        count+=1
        print(count)
        await asyncio.sleep(1)
    await context.write_and_drain_async(b"end of data")
    print("end")
    return True

@app.web_action()
async def process_web_action_async(context: edge.WebContext):
    return "Hi from simple web server"

app.listening()
