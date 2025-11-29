from bclib import edge


if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "restful",
        "log_error": True,
        "log_request": True
    }


app = edge.from_options(options)


@app.restful_handler()
def process_default_rest_action(_: edge.RESTfulContext):
    raise edge.BadRequestErr(data={
        "status_code": edge.HttpStatusCodes.BAD_REQUEST,
        "error": "bad request"
    })


app.listening()
