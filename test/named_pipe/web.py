
from bclib import edge


options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "router":  "web",
    "settings": {
        "connections.named_pipe.demo": "//./pipe/ABC"
    }
}

app = edge.from_options(options)


@app.web_action()
async def process_web_request_async(context: edge.WebContext):
    print("process_web_request")
    pipe = context.dispatcher.db_manager.get_named_pipe_connection("demo")
    #pipe.try_send_command({"id": 123})
    data = await pipe.try_send_query_async({"id": 123})
    return data


app.listening()
