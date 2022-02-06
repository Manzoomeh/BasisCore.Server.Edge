import asyncio
from bclib import edge


options = {
    # "sender": "127.0.0.1:1025",
    # "receiver": "127.0.0.1:1026",
    "server": "localhost:8080",
    "router": "restful",
    "settings": {
        "connections.rest.rest_demo": "http://127.0.0.1:8080/inner_api"
    }
}


app = edge.from_options(options)


@app.restful_action(app.url("inner_api"))
def process_default_web_action(context: edge.RESTfulContext):
    return context.query


@app.restful_action()
async def process_default_web_action_async(context: edge.RESTfulContext):
    api = context.open_restful_connection("rest_demo")
    print("1", asyncio.get_running_loop())
    data = await api.post_async(params={"name": "ali"})
    await asyncio.sleep(2)
    print("2")
    return {"data": "result from process_default_web_action", "param": data}


app.listening()
