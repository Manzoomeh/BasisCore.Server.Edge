import asyncio
from bclib import edge


options = {
    # "sender": "127.0.0.1:1025",
    # "receiver": "127.0.0.1:1026",
    "http": "localhost:8080",
    "router": "restful",
    "settings": {
        "connections.rest.rest_demo": "http://127.0.0.1:8080/inner_api"
    }
}


app = edge.from_options(options)


@app.restful_handler(app.url("inner_api"))
def process_default_web_handler(context: edge.RESTfulContext):
    return context.query


@app.restful_handler()
async def process_default_web_handler_async(context: edge.RESTfulContext):
    api = context.open_restful_connection("rest_demo")
    data = await api.post_async(params={"name": "ali"})
    await asyncio.sleep(2)
    return {"data": "result from process_default_web_handler", "param": data}


app.listening()
