import context
import dispatcher

options = {
    "sender": {
        "ip": "127.0.0.1",
        "port": 1025,
    },
    "receiver": {
        "ip": "127.0.0.1",
        "port": 1026,
    },
    "router": {
        "client_source": ["*"],
    }
}

app = dispatcher.SocketDispatcher(options)


@ app.source_action(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"))
def process_basiscore_source(context: context.ClientSourceContext):
    print("process_basiscore_source",  context)

    return [
        {"id": 1, "name": "Data1"},
        {"id": 2, "name": "Data2"},
        {"id": 3, "name": "Data3"},
        {"id": 4, "name": "Data4"}
    ]


@app.source_action(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: context.ClientSourceContext):
    print("process1 ",  context)
    data = [
        {"id": 1, "name": "Data1"},
        {"id": 2, "name": "Data2"},
        {"id": 3, "name": "Data3"},
        {"id": 4, "name": "Data4"},
        {"id": 5, "name": "Data5"},
        {"id": 6, "name": "Data6"}
    ]
    return data


@app.source_member_action(
    app.in_list("context.command.source", "basiscore", "demo"),
    app.equal("context.member.name", "list")
)
def process_list_member(context: context.ClientSourceMemberContext):
    print("process_list_member")
    return context.data


@app.source_member_action(
    app.in_list("context.command.source", "basiscore", "demo"),
    app.equal("context.member.name", "paging")
)
def process_page_member(context: context.ClientSourceMemberContext):
    data = {
        "total": len(context.data),
        "from": 0,
        "to": len(context.data)-1,
    }
    print("process_page_member")
    return data


@app.source_member_action(
    app.equal("context.command.source", "basiscore"),
    app.equal("context.member.name", "count")
)
def process_count_member(context: context.ClientSourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data


p = {
    "form": {
        "command": "<basis core=\"dbsource\" source=\"basiscore\" mid=\"20\" name=\"db\" lid=\"1\" userid=\"122503\" ownerid=\"8044\" gid=\"\" catid=\"\" q=\"\" dmnid=\"\" ownerpermit=\"\" rkey=\"D77766EC-3733-4BF1-99B4-003EE8E8106C\" usercat=\"241\">\n  <member name=\"list\" type=\"list\" pageno=\"3\" perpage=\"20\" request=\"catname\" order=\"id desc\" />\n  <member name=\"paging\" type=\"list\" request=\"paging\" count=\"5\" parentname=\"list\" />\n  <member name=\"count\" type=\"scalar\" request=\"count\" />\n</basis>",
        "dmnid": "20"
    }
}

app.listening()
