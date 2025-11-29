from bclib import edge


options = {
    "http": "localhost:8080",
    "router": "restful",
}


app = edge.from_options(options)


@app.restful_handler()
async def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    data_1 = 12
    data_2 = "ok"
    await context.dispatcher.log_async(**locals(), data_3="333", schema_name=1161)
    return {"result": "ok"}


app.listening()
