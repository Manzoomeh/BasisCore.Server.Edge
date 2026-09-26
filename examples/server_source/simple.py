"""Server-source handlers over HTTP (router=server_source)."""
from bclib import edge
from bclib.context import ServerSourceContext, ServerSourceMemberContext

options = {
    "name": "server-source",
    "http": "localhost:9171",
    "router": "server_source",
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


@app.server_source_handler(app.equal("context.command.name", "demo"))
def process_demo(_: ServerSourceContext):
    return generate_data()


@app.server_source_member_handler(app.equal("context.member.name", "list"))
def process_list(context: ServerSourceMemberContext):
    return context.data


@app.server_source_member_handler(app.equal("context.member.name", "count"))
def process_count(context: ServerSourceMemberContext):
    return {"count": len(context.data)}


if __name__ == "__main__":
    print("Server source listening on http://localhost:9171/")
    app.listening()
