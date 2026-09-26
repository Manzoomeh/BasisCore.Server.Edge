"""InternalServerErr with custom payload."""
from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import InternalServerErr

options = {
    "name": "ex-custom",
    "http": "localhost:9144",
    "router": "restful",
    "log_error": True,
}

app = edge.from_options(options)


@app.restful_handler()
def process_default(_: RESTfulContext):
    raise InternalServerErr(
        None,
        {
            "code": "12-33",
            "type": "custom",
            "msg": "error message",
        },
    )


if __name__ == "__main__":
    print("Custom InternalServerErr -> http://localhost:9144/")
    app.listening()
