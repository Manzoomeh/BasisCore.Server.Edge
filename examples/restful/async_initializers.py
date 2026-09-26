"""Async-style init: load data before listening (current listening() has no hooks)."""
import asyncio

from bclib import edge
from bclib.context import RESTfulContext

options = {
    "name": "rest-async-init",
    "http": "localhost:9131",
    "router": "restful",
}

app = edge.from_options(options)
data: list = []


async def load_data_async() -> list:
    import random
    import string

    for i in range(10):
        data.append({
            "id": i,
            "data": "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        })
        await asyncio.sleep(0.01)
    print("data loaded!", len(data))
    return data


@app.restful_handler(app.url(":id"))
def by_id(context: RESTfulContext):
    item_id = int(context.url_segments.id)
    return [row for row in data if row["id"] == item_id]


@app.restful_handler()
def all_items(context: RESTfulContext):
    return data


if __name__ == "__main__":
    asyncio.run(load_data_async())
    print("REST async-init -> http://localhost:9131/")
    app.listening()
