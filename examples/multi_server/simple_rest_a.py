from bclib import edge

options = {
    "name": "multi-a",
    "http": "localhost:9187",
    "router": "restful",
    "log_request": True,
}

app = edge.from_options(options)


@app.cache()
def generate_data() -> list:
    import random
    import string

    return [
        {
            "id": i,
            "data": "".join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        }
        for i in range(10)
    ]


@app.restful_handler()
def process_restful_request(_: edge.RESTfulContext):
    return generate_data()


if __name__ == "__main__":
    print("multi-a -> http://localhost:9187/")
    app.listening()
