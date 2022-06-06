from bclib import edge


options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_request": False,
    "settings": {
        "connections.named_pipe.demo": "//./pipe/ABC"
    }
}

app = edge.from_options(options)


@app.restful_action()
async def process_restful_request_async(context: edge.RESTfulContext):
    print("process_restful_request")
    pipe = context.dispatcher.db_manager.get_named_pipe_connection("demo")
    #pipe.try_send_command({"id": 123})
    data = await pipe.try_send_query_async({"id": 123})
    return data


app.listening()
