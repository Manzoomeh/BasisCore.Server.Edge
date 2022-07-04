from bclib import edge


options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_request": False
}

app = edge.from_options(options)


@app.restful_action()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return generate_data()


app.listening()
