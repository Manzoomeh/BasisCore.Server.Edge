"""Large JSON body + CLIENT_MAX_SIZE configuration."""
import json

from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import BadRequestErr
from bclib.listener.http.http_listener import HttpListener

options = {
    "name": "restful-large-body",
    "http": "localhost:9133",
    "configuration": {HttpListener.CLIENT_MAX_SIZE: 1024**4},
    "router": "restful",
}

app = edge.from_options(options)


@app.restful_handler()
def process_post(context: RESTfulContext):
    body = context.body
    if body is None:
        raise BadRequestErr(
            message="empty body",
            data={"result": "incorrect inputs"},
        )
    return {"result": len(json.dumps(body, ensure_ascii=False))}


if __name__ == "__main__":
    print("Large body -> POST http://localhost:9133/")
    app.listening()
