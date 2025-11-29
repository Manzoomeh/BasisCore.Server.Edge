from bclib import edge

if "options" not in dir():
    options = {
        "http": "localhost:8080",
        "router": {
            "restful": ["*"],
        },
        "settings": {

            "connections.rest.rest_demo": "http://localhost:8080/rest",

        }
    }


app = edge.from_options(options)


@app.cache()
def generate_data() -> list:
    import string
    import random  # define the random module

    ret_val = list()
    for i in range(10):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


###########################################
# rest
###########################################


@app.restful_handler(
    app.url("/:id"))
def process_restful_1(context: edge.RESTfulContext):
    print("process_restful_1")
    id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == id]


@app.restful_handler(
    app.url(":id"))
def process_restful_2(context: edge.RESTfulContext):
    print("process_restful_2")
    id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == id]


@app.restful_handler(
    app.url(""))
def process_restful_3(context: edge.RESTfulContext):
    print("process_restful_3")

    return generate_data()


@app.restful_handler(
    app.url("alI/:p/m/:l"))
def process_restful_5(context: edge.RESTfulContext):
    print("process_restful_5")
    return generate_data()


@app.restful_handler(
    app.url("ali/:p/m"))
def process_restful_4(context: edge.RESTfulContext):
    print("process_restful_4")
    return generate_data()


@app.restful_handler(
    app.url("ali/:p/M/:*l"))
def process_restful_6(context: edge.RESTfulContext):
    print("process_restful_6")
    return generate_data()


@app.restful_handler()
def process_restful_else(context: edge.RESTfulContext):
    print("process_restful_else")
    return generate_data()


app.listening()
