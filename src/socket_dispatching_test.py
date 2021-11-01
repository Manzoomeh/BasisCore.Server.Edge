import json
from pathlib import Path
from dispatcher import SocketDispatcher
from context import SourceContext, SourceMemberContext


with open(Path(__file__).with_name("host.json"), encoding='UTF-8') as options_file:
    options = json.load(options_file)

app = SocketDispatcher(options)


@app.source_action(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"))
def process_basiscore_source(context: SourceContext):
    print("process1 ",  context)
    # data = [
    #     {"id": 1, "name": "Data1"},
    #     {"id": 2, "name": "Data2"},
    #     {"id": 3, "name": "Data3"},
    #     {"id": 4, "name": "Data4"}
    # ]
    db = context.open_sql_connection("sql_demo")
    with db:
        cursor = db.connection.cursor()
        cursor.execute("""
    SELECT TOP (20) [Id]
        ,[InsCode]
        ,[ISIN]
        ,[CISIN]
        ,[Name]
        ,[Symbol]
    FROM [MarketData].[dbo].[Shares]""")

        result = [dict(zip([column[0] for column in cursor.description], row))
                  for row in cursor.fetchall()]
    return result


@app.source_action(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: SourceContext):
    print("process1 ",  context)
    db = context.open_sqllite_connection("sqlite_demo")
    with db:
        cursor = db.connection.cursor()
        cursor.execute("""
    SELECT  [Id]
        ,[InsCode]
        ,[ISIN]
        ,[CISIN]
        ,[Name]
        ,[Symbol]
    FROM [Shares]""")

        data = [dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()]

    # data = [
    #     {"id": 44, "name": "Data 44", "age": 22},
    #     {"id": 66, "name": "Data 66", "age": 50},
    #     {"id": 76, "name": "Data 76", "age": 30},
    #     {"id": 89, "name": "Data 89", "age": 52},
    #     {"id": 70, "name": "Data 70", "age": 37},
    #     {"id": 40, "name": "Data 40", "age": 45}
    # ]
    return data


@app.source_member_action(
    app.equal("context.member.name", "list")
)
@app.cache(key="member-list")
def process_list_member(context: SourceMemberContext):
    print("process_list_member")
    return context.data


@app.source_member_action(
    app.equal("context.member.name", "paging")
)
@app.cache(10)
def process_page_member(context: SourceMemberContext):
    data = {
        "total": len(context.data),
        "from": 0,
        "to": len(context.data)-1,
    }
    print("process_page_member")
    return data


@app.source_member_action(
    app.equal("context.member.name", "count")
)
def process_count_member(context: SourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data


@app.source_member_action()
def all_member_process(_: SourceMemberContext):
    print("all_member_process", )
    return None


app.listening()
