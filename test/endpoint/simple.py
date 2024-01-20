
import asyncio
from concurrent.futures import thread
from bclib import edge
import time


options = {
    "endpoint": "127.0.0.1:1026",
    "router":  "restful"
}


app = edge.from_options(options)


@app.restful_action()
def sabt_document(context: edge.RESTfulContext):
    print('end')
    return {"data": "isOk"}


app.listening()
