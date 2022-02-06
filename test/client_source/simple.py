import asyncio
from bclib import edge


options = {
    "server": "localhost:8080",
    "router": "client_source"
}

app = edge.from_options(options)

# sample request
#############
command = '''
<basis core='dbsource' run='atclient' source='basiscore' mid='20' name='demo'  lid='1' dmnid='' ownerpermit='' >
        <member name='list' type='list' pageno='3' perpage='20' request='catname' order='id desc'></member>
        <member name='paging' type='list' request='paging' count='5' parentname='list'></member>
        <member name='count' type='scalar' request='count' ></member>
</basis>
'''

dmnid = 0
#############


@app.cache()
def generate_data() -> list:
    import string
    import random  # define the random module

    ret_val = list()
    for i in range(10):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


@app.client_source_action(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"))
async def process_basiscore_source(context: edge.ClientSourceContext):
    print("process_basiscore_source")
    await asyncio.sleep(2)
    return generate_data()


@app.client_source_action(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: edge.ClientSourceContext):
    return [row for row in generate_data() if row["id"] < 5]


@app.client_source_member_action(
    app.equal("context.member.name", "list")
)
def process_list_member(context: edge.ClientSourceMemberContext):
    print("process_list_member")
    return context.data


@app.client_source_member_action(
    app.equal("context.member.name", "paging")
)
def process_page_member(context: edge.ClientSourceMemberContext):
    data = {
        "total": len(context.data),
        "from": 0,
        "to": len(context.data)-1,
    }
    print("process_page_member")
    return data


@app.client_source_member_action(
    app.equal("context.member.name", "count")
)
def process_count_member(context: edge.ClientSourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data


app.listening()
