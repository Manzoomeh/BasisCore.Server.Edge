from bclib import edge


if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "restful",
        "log_error": True,
        "log_request": True
    }


app = edge.from_options(options)


@ app.restful_action()
def process_default_rest_action(context: edge.RESTfulContext):
    error_data = {
        "code": "12-33",
        "type": "custom",
        "msg": "error message"
    }
    raise edge.InternalServerErr(None, error_data)


app.listening()
