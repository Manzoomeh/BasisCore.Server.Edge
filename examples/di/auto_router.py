"""Auto router — register handlers; no explicit router map required for demos."""
from bclib import edge
from bclib.context import RESTfulContext

app = edge.from_options({
    "name": "di-auto-router",
    "http": "localhost:9104",
    "router": "restful",
})


@app.restful_handler("api/users", method="GET")
def get_users():
    return {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}


@app.restful_handler("api/users/:id", method="GET")
def get_user(context: RESTfulContext):
    return {"user": {"id": context.url_segments["id"], "name": "Alice"}}


if __name__ == "__main__":
    print("Auto router -> http://localhost:9104/api/users")
    app.listening()
