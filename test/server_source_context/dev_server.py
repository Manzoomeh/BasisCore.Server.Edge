from bclib import edge

if "options" not in dir():
    options = {
        "sender": {
            "ip": "127.0.0.1",
            "port": 1025,
        },
        "receiver": {
            "ip": "127.0.0.1",
            "port": 1026,
        },
        "router": "server_dbsource"
    }


app = edge.from_options(options)


@ app.cache()
def generate_data() -> list:
    import string
    import random  # define the random module

    ret_val = list()
    for i in range(10):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


@ app.server_source_action()
def process_basiscore_source(context: edge.ServerSourceContext):
    print("process_basiscore_source")
    return generate_data()


@ app.server_source_action(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: edge.ServerSourceContext):
    return [row for row in generate_data() if row["id"] < 5]


@app.server_source_member_action(
    app.equal("context.member.name", "list")
)
def process_list_member(context: edge.ServerSourceMemberContext):
    print("process_list_member")
    return context.data


@app.server_source_member_action(
    app.equal("context.member.name", "paging")
)
def process_page_member(context: edge.ServerSourceMemberContext):
    data = {
        "total": len(context.data),
        "from": 0,
        "to": len(context.data)-1,
    }
    print("process_page_member")
    return data


@app.server_source_member_action(
    app.equal("context.member.name", "count")
)
def process_count_member(context: edge.ServerSourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data


app.listening()
