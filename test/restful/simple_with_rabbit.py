import edge


options = {
    "http": "localhost:8080",
    "router": {
        "rabbit": [
            {
                "url": "amqp://guest:guest@localhost:5672",
                "queue": "hello"
            }
        ],
        "restful": ["*"]
    }
}

app = edge.from_options(options)


@app.cache()
def generate_data() -> list:
    import string
    import random

    ret_val = list()
    for i in range(10):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


@app.restful_handler(
    app.url(":id"))
def process_restful_with_filter_request(context: edge.RESTfulContext):
    print("process_restful_with_filter_request")
    id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == id]


@app.restful_handler()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return generate_data()


app.listening()
