
import asyncio
import time
from concurrent.futures import thread
from typing import Optional

from bclib import edge

options = {
    "server": "localhost:8080",
    "endpoint": "127.0.0.1:1025",
    # "router":  "web"
    "error_log": True
}

app = edge.from_options(options)


@app.web_action("test00")
async def test_handler_0():
    return "<h1>Test endpoint 00</h1>"


@app.action("test0")
async def test_web_handler_0():
    return {
        "message": "Test endpoint 1",
        "status": "success"
    }


@app.restful_action("test1")
async def test_handler_1():
    return {
        "message": "Test endpoint 1",
        "status": "success"
    }


@app.restful_action("test2", method=["POST", "PUT"])
async def test_handler_3(context: edge.RESTfulContext):
    return {
        "message": "Test endpoint 3",
        "received": context.response_type
    }


@app.restful_action("test2")
async def test_handler_2(context: edge.RESTfulContext, id: Optional[int] = None):
    return {
        "message": "Test endpoint 2",
        "id": id,
        "params": context.query
    }


@app.web_action()
async def process_web_remain_request():
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
            """

app.listening()
