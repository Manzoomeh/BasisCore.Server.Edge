"""ForbiddenErr (403) demo."""
from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import ForbiddenErr
from bclib.utility import HttpStatusCodes

options = {
    "name": "ex-forbidden",
    "http": "localhost:9142",
    "router": "restful",
    "log_error": True,
}

app = edge.from_options(options)


@app.restful_handler()
def process_default(_: RESTfulContext):
    raise ForbiddenErr(
        data={
            "status_code": HttpStatusCodes.FORBIDDEN,
            "error": "forbidden",
        }
    )


if __name__ == "__main__":
    print("Forbidden -> http://localhost:9142/")
    app.listening()
