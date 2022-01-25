import edge


options = {
    "server": "localhost:8080",
    "router": "restful"
}

app = edge.from_options(options)

DATA_COUNT = 10


@app.cache()
def generate_data() -> list:
    import string
    import random  # define the random module

    ret_val = list()
    for i in range(DATA_COUNT):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


def check_id(context: edge.RESTfulContext):
    id = int(context.url_segments.id)
    if(id < 0 or id > DATA_COUNT):
        raise edge.UnauthorizedErr(
            f"id must be between 0 than {DATA_COUNT} .(current value id= {id} )!")
    return True


@app.restful_action(
    app.url(":id"),
    app.callback(check_id)
)
def process_restful_with_filter_request(context: edge.RESTfulContext):
    print("process_restful_with_filter_request")
    id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == id]


@app.restful_action()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return generate_data()


app.listening()
