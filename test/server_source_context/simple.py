import datetime
import json
import xml.etree.ElementTree

import edge

options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "defaultRouter": "server_source",
    "router": {
        "web": ["*"],
    }
}

app = edge.from_options(options)


@app.cache()
def generate_data() -> list:
    import random  # define the random module
    import string

    ret_val = list()
    for i in range(10):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


######################
# Server source
######################


@app.server_source_handler(app.equal("context.command.name", "demo"))
def process_basiscore_server_source(context: edge.ServerSourceContext):
    print("process_basiscore_source", context.params.p1)
    return generate_data()


@app.server_source_handler(
    app.equal("context.command.name", "basiscode"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: edge.ServerSourceContext):
    return [row for row in generate_data() if row["id"] < 5]


@app.server_source_member_handler(
    app.equal("context.member.name", "list")
)
def process_list_server_member(context: edge.ServerSourceMemberContext):
    print("process_list_member")
    return context.data


@app.server_source_member_handler(
    app.equal("context.member.name", "paging")
)
def process_page_server_member(context: edge.ServerSourceMemberContext):
    data = {
        "total": len(context.data),
        "from": 0,
        "to": len(context.data)-1,
    }
    print("process_page_member")
    return data


@app.server_source_member_handler(
    app.equal("context.member.name", "count")
)
def process_count_server_member(context: edge.ServerSourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data


#####
# Web
#####

@app.web_handler()
def process_web_sample_dbsource_request(context: edge.HttpContext):
    context.response_type = edge.ResponseTypes.RENDERABLE
    return """
     <basis core="dbsource"  source="cmsDbService" mid="20" name="demo"  lid="1" dmnid="" ownerpermit="" >
        <member name="list" type="list" pageno="3" perpage="20" request="catname" order="id desc"></member>
        <member name="paging" type="list" request="paging" count="5" parentname="list"></member>
        <member name="count" type="scalar" request="count" ></member>
        <params>
            <add name='p1' value='v1' ></add>
            <add name='p2' value='v2' ></add>
        </params>
     </basis>
     [##demo.count.count##]
     <br/>
[##demo.list.id##]
        """


app.listening()
