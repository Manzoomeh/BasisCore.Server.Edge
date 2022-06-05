from bclib import edge


options = {
    "named_pipe": "//./pipe/ABC",
    "router": "named_pipe",
    "log_request": False
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


@app.named_pipe_action()
def process_restful_request(context: edge.NamedPipeContext):
    print("process_restful_request", context.message)
    return generate_data()


app.listening()
