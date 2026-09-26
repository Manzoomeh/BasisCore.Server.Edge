"""BadRequestErr (400) demo."""
from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import BadRequestErr
from bclib.utility import HttpStatusCodes

options = {
    "name": "ex-bad-request",
    "http": "localhost:9141",
    "router": "restful",
    "log_error": True,
}

app = edge.from_options(options)


@app.restful_handler()
def process_default(_: RESTfulContext):
    raise BadRequestErr(
        data={
            "status_code": HttpStatusCodes.BAD_REQUEST,
            "error": "bad request",
        }
    )


if __name__ == "__main__":
    print("BadRequest -> http://localhost:9141/")
    app.listening()
