
import asyncio
from concurrent.futures import thread
from bclib import edge
import time


options = {
    "endpoint": "127.0.0.1:1025",
    "router":  "web"
}

app = edge.from_options(options)

print(app)


@app.web_action()
async def process_web_remain_request(context: edge.WebContext):
    # await asyncio.sleep(1)
    # def f(n):
    #     time.sleep(n)
    #     return "33"

    # k = await context.dispatcher.run_in_background(asyncio.sleep, 1)
    # time.sleep(1)
    # time.sleep(1)
    # print("process_web_remain_request")
    return """
        <form method="post" enctype="multipart/form-data">
<input type="file" name="my_files" multiple="multiple"/>
<input type="submit"/>
</form>
            """*500


app.listening()
