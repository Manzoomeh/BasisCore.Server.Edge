import json

from bclib import edge
from bclib.listener.http.http_listener import HttpListener

options = {
    "server": "localhost:8080",
    "configuration": {
        HttpListener.CLIENT_MAX_SIZE: 1024**4
    },
    "router": "restful"
}


app = edge.from_options(options)


@app.restful_handler()
def process_post(context: edge.RESTfulContext):
    body = context.body
    if body is None:
        raise edge.BadRequestErr(
            message="empty body",
            data={
                "result": "incorrect inputs"
            }
        )
    return {
        "result": len(json.dumps(body, ensure_ascii=False))
    }


app.listening()
