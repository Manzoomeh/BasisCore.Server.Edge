import json
from pathlib import Path
from context.web_context import WebContext
from dispatcher import SocketDispatcher
from context import SourceContext, SourceMemberContext, RESTfulContext


with open(Path(__file__).with_name("host.json"), encoding='UTF-8') as options_file:
    options = json.load(options_file)

app = SocketDispatcher(options)


@app.web_action()
def process_basiscore_web(context: WebContext):
    print("process_basiscore_restful1")
    return "<h1>Hello world!</h1>"


@app.restful_action(
    app.in_list("context.body.id", 10))
def process_basiscore_restful1(context: RESTfulContext):
    ret_val = dict()
    ret_val["client"] = context.body
    ret_val["message"] = "hello world!10"
    return ret_val


@app.restful_action(
    app.in_list("context.body.id", 12),
    app.equal("context.body.age", 13))
def process_basiscore_restful2(context: RESTfulContext):
    ret_val = dict()
    ret_val["client"] = context.body
    ret_val["message"] = "hello world!12-age"
    return ret_val


@app.restful_action(
    app.in_list("context.body.id", 12))
def process_basiscore_restful3(context: RESTfulContext):
    ret_val = dict()
    ret_val["client"] = context.body
    ret_val["message"] = "hello world!12"
    return ret_val


@app.restful_action()
def process_basiscore_restful4(context: RESTfulContext):
    ret_val = dict()
    ret_val["message"] = "hello world! - No match"
    return ret_val


@app.source_action(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"))
def process_basiscore_source(context: SourceContext):
    print("process1 ",  context)
    data = [
        {"id": 1, "name": "Data1"},
        {"id": 2, "name": "Data2"},
        {"id": 3, "name": "Data3"},
        {"id": 4, "name": "Data4"}
    ]
    return data


@app.source_action(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: SourceContext):
    print("process1 ",  context)

    # sql server
    # db = context.open_sql_connection("sql_demo")
    # with db:
    #     cursor = db.connection.cursor()
    #     cursor.execute("""
    # SELECT TOP (20) [Id]
    #     ,[InsCode]
    #     ,[ISIN]
    #     ,[CISIN]
    #     ,[Name]
    #     ,[Symbol]
    # FROM [MarketData].[dbo].[Shares]""")

    #     data = [dict(zip([column[0] for column in cursor.description], row))
    #             for row in cursor.fetchall()]

    # sqlite
    # db = context.open_sqllite_connection("sqlite_demo")
    # with db:
    #     cursor = db.connection.cursor()
    #     cursor.execute("""
    # SELECT  [Id]
    #     ,[InsCode]
    #     ,[ISIN]
    #     ,[CISIN]
    #     ,[Name]
    #     ,[Symbol]
    # FROM [Shares]""")
    #     data = [dict(zip([column[0] for column in cursor.description], row))
    #             for row in cursor.fetchall()]

    # mongo
    # db = context.open_mongo_connection("mongo_demo")
    # with db:
    #     data = [{"id": i, "data": d}
    #             for i, d in enumerate(db.client.list_database_names())]

    data = [
        {"id": 44, "name": "Data 44", "age": 22},
        {"id": 66, "name": "Data 66", "age": 50},
        {"id": 76, "name": "Data 76", "age": 30},
        {"id": 89, "name": "Data 89", "age": 52},
        {"id": 70, "name": "Data 70", "age": 37},
        {"id": 40, "name": "Data 40", "age": 45}
    ]
    return data


@app.source_member_action(
    app.equal("context.member.name", "list")
)
# @app.cache(key="member-list")
def process_list_member(context: SourceMemberContext):
    print("process_list_member")
    return context.data


@app.source_member_action(
    app.equal("context.member.name", "paging")
)
# @app.cache(10)
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
