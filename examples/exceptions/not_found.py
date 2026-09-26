"""NotFoundErr demo."""
from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import NotFoundErr

options = {
    "name": "ex-not-found",
    "http": "localhost:9140",
    "router": "restful",
    "log_error": True,
}

app = edge.from_options(options)


@app.restful_handler("api/item/:id", method="GET")
def get_item(context: RESTfulContext):
    raise NotFoundErr(f"item {context.url_segments['id']} not found")


if __name__ == "__main__":
    print("NotFound -> http://localhost:9140/api/item/1")
    app.listening()
