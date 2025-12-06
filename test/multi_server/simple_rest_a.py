from bclib import edge

options = {
    "http": "localhost:8082",
    "router": "restful",
    "log_request": True
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


@app.restful_handler()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return generate_data()


app.listening()
