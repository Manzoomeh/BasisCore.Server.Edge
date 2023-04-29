from bclib import edge


options = {
    "endpoint": "127.0.0.1:1026",
    "router": "restful",
    "log_request": True
}

app = edge.from_options(options)


@app.restful_action()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return {"data": 123}


app.listening()
