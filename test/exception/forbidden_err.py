from bclib import edge


if "options" not in dir():
    options = {
        "http": "localhost:8080",
        "router": "restful",
        "log_error": False,
        "log_request": True
    }


app = edge.from_options(options)


@app.restful_handler()
def process_default_rest_action(_: edge.RESTfulContext):
    raise edge.ForbiddenErr(data={
        "status_code": edge.HttpStatusCodes.FORBIDDEN,
        "error": "forbidden"
    })


app.listening()
