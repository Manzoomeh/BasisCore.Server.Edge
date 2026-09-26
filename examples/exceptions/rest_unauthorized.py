"""UnauthorizedErr from a REST callback predicate."""
from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import UnauthorizedErr

DATA_COUNT = 10

options = {
    "name": "ex-rest-unauth",
    "http": "localhost:9146",
    "router": "restful",
    "log_error": True,
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
        for i in range(DATA_COUNT)
    ]


async def check_id(context: RESTfulContext) -> bool:
    item_id = int(context.url_segments.id)
    if item_id < 0 or item_id >= DATA_COUNT:
        raise UnauthorizedErr(
            f"id must be between 0 and {DATA_COUNT - 1} (got {item_id})"
        )
    return True


@app.restful_handler(app.url(":id"), app.callback(check_id))
def by_id(context: RESTfulContext):
    item_id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == item_id]


@app.restful_handler()
def all_items(_: RESTfulContext):
    return generate_data()


if __name__ == "__main__":
    print("REST unauthorized -> http://localhost:9146/99")
    app.listening()
