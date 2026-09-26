"""Minimal REST + in-memory @app.cache()."""
from bclib import edge
from bclib.context import RESTfulContext

options = {
    "name": "restful-simple",
    "http": "localhost:9132",
    "router": "restful",
    "log_request": False,
}

app = edge.from_options(options)


@app.cache()
def generate_data() -> list:
    import random
    import string

    return [
        {
            "id": i,
            "data": "".join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        }
        for i in range(10)
    ]


@app.restful_handler(app.url(":id"))
def by_id(context: RESTfulContext):
    item_id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == item_id]


@app.restful_handler()
def all_items(_: RESTfulContext):
    return generate_data()


if __name__ == "__main__":
    print("REST simple -> http://localhost:9132/  and /3")
    app.listening()
