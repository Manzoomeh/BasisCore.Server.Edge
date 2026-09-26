"""Client-source (dbsource) handlers — starts HTTP; call with BasisCore command form."""
import asyncio

from bclib import edge
from bclib.context import ClientSourceContext, ClientSourceMemberContext

options = {
    "name": "client-source",
    "http": "localhost:9170",
    "router": "client_source",
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


@app.client_source_handler(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"),
)
async def process_basiscore_source(_: ClientSourceContext):
    await asyncio.sleep(0.05)
    return generate_data()


@app.client_source_handler(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"),
)
def process_demo_source(_: ClientSourceContext):
    return [row for row in generate_data() if row["id"] < 5]


@app.client_source_member_handler(app.equal("context.member.name", "list"))
def process_list_member(context: ClientSourceMemberContext):
    return context.data


@app.client_source_member_handler(app.equal("context.member.name", "paging"))
def process_page_member(context: ClientSourceMemberContext):
    return {"total": len(context.data), "from": 0, "to": max(len(context.data) - 1, 0)}


@app.client_source_member_handler(app.equal("context.member.name", "count"))
def process_count_member(context: ClientSourceMemberContext):
    return {"count": len(context.data)}


if __name__ == "__main__":
    print("Client source listening on http://localhost:9170/")
    app.listening()
