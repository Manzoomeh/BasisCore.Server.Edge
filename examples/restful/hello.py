"""REST hello — smallest runnable API."""
from bclib import edge
from bclib.context import RESTfulContext

app = edge.from_options({
    "name": "rest-hello",
    "http": "localhost:9130",
    "router": "restful",
    "log_error": True,
})


@app.restful_handler("api/hello", method="GET")
def hello(context: RESTfulContext):
    return {"message": "Hello BasisEdge", "url": context.url}


if __name__ == "__main__":
    print("REST hello -> http://localhost:9130/api/hello")
    app.listening()
