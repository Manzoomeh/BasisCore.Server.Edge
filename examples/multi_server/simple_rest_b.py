from bclib import edge

options = {
    "name": "multi-b",
    "http": "localhost:9188",
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
        for i in range(5)
    ]


@app.restful_handler()
def process_restful_request(_: edge.RESTfulContext):
    return {"server": "b", "rows": generate_data()}


if __name__ == "__main__":
    print("multi-b -> http://localhost:9188/")
    app.listening()
