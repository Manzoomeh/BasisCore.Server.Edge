from bclib import edge

# if "options" not in dir():
#     options = {
#         "server":"localhost:8080",
#         "router": {
#             "restful": ["*"],
#         },
#         "settings": {

#             "connections.rest.rest_demo": "http://localhost:8080/rest",

#         }
#     }
options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "router": {
        "restful": ["*"],
    },
    "settings": {

        "connections.rest.rest_demo": "http://127.0.0.1:1564/rest",

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
    app.url("rest/:id"))
def process_restful_with_filter_request(context: edge.RESTfulContext):
    print("process_restful_with_filter_request")
    id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == id]


@app.restful_handler(app.url("rest"))
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    context.open_restful_connection("rest_demo").get(segment="/12")
    return generate_data()


@app.restful_handler()
def process_else_request(context: edge.RESTfulContext):
    print("process_else_request")
    return generate_data()


app.listening()
