import json
from pathlib import Path
from context import ClientSourceContext, ClientSourceMemberContext
from dispatcher import Dispatcher


with open(Path(__file__).with_name("host.json"), encoding='UTF-8') as options_file:
    options = json.load(options_file)

app = Dispatcher(options)


@ app.source_action(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"))
def process_basiscore_source(context: ClientSourceContext):
    print("process_basiscore_source",  context)

    # sql_connection = context.open_sql_connection("sql_demo")
    # sqlite_connection = context.open_sqllite_connection("sqlite_demo")
    # with sqlite_connection, sqlite_connection:
    #     with sql_connection.connection.cursor() as cursor:
    #         rows = cursor.execute("""
    #     SELECT TOP (10) [Id]
    #         ,[InsCode]
    #         ,[ISIN]
    #         ,[CISIN]
    #         ,[Name]
    #         ,[Symbol]
    #     FROM [MarketData].[dbo].[Shares]""").fetchall()

    #     cursor = sqlite_connection.connection.cursor()
    #     cursor.execute(
    #         '''CREATE TABLE Shares (Id ,InsCode ,ISIN ,CISIN ,Name ,Symbol )''')
    #     sqlite_connection.connection.commit()
    #     for p in rows:
    #         cursor.execute(
    #             "insert into Shares values (?, ?,?,?,?,?)", p)

    #     sqlite_connection.connection.commit()

    # mongo
    # db = context.open_mongo_connection("mongo_demo")
    # with db:
    #     print([{"id": i, "data": d}
    #           for i, d in enumerate(db.client.list_database_names())])

    # RESTful
    # db = context.open_restful_connection("rest_demo")
    # with db:
    #     data = db.get()

    # db = context.open_restful_connection("check_rkey")
    # with db:
    #     data = db.post(segment='/EC9CC11F-9936-4495-AAA5-58C3C18D8373')
    #     print(data)

    # Rabbit
    # db = context.open_rabbit_connection("rabbit_test")
    # with db:
    #     msg = dict()
    #     msg["type"] = "clear-cache"
    #     msg["keys"] = ["member-list"]
    #     db.publish(msg)

    data = [
        {"id": 1, "name": "Data1"},
        {"id": 2, "name": "Data2"},
        {"id": 3, "name": "Data3"},
        {"id": 4, "name": "Data4"}
    ]

    # def task(delay):
    #     print("start for {0}".format(delay))
    #     time.sleep(delay)
    #     print("end for {0}".format(delay))

    # app.run_in_background(task, 1)
    # app.run_in_background(task, 3)
    # app.run_in_background(task, 2)
    return data


@app.source_action(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: ClientSourceContext):
    print("process1 ",  context)
    data = [
        {"id": 1, "name": "Data1"},
        {"id": 2, "name": "Data2"},
        {"id": 3, "name": "Data3"},
        {"id": 4, "name": "Data4"}
    ]
    return data


@app.source_member_action(
    app.equal("context.command.source", "basiscore"),
    app.equal("context.member.name", "list")
)
def process_list_member(context: ClientSourceMemberContext):
    print("process_list_member")
    return context.data


@app.source_member_action(
    app.equal("context.command.source", "basiscore"),
    app.equal("context.member.name", "paging")
)
def process_page_member(context: ClientSourceMemberContext):
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
def process_count_member(context: ClientSourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data


@app.source_member_action()
def all_member_process(_: ClientSourceMemberContext):
    print("all_member_process", )
    return None


p = {
    "cms": {
        "request": {
            "methode": "post",
            "rawurl": "api/C0033824-7E6B-484B-82F9-BEC64192FD1E",
            "url": "api/C0033824-7E6B-484B-82F9-BEC64192FD1E",
            "cache-control": "no-cache",
            "postman-token": "adbac938-fa16-4c20-9575-a4a7e0a75bec",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "PostmanRuntime/6.4.1",
            "accept": "/",
            "full-url": " basispanel.ir/api/C0033824-7E6B-484B-82F9-BEC64192FD1E",
            "host": " basispanel.ir",
            "accept-encoding": "gzip, deflate",
            "content-length": "744",
            "connection": "keep-alive",
            "request-id": "149379",
            "hostip": "185.44.36.193",
            "hostport": "80",
            "clientip": "188.158.15.78",
            "body": "command=%3Cbasis%20core%3D%22dbsource%22%20source%3D%22basiscore%22%20mid%3D%2220%22%20name%3D%22db%22%20lid%3D%221%22%20userid%3D%22122503%22%20ownerid%3D%228044%22%20gid%3D%22%22%20catid%3D%22%22%20q%3D%22%22%20dmnid%3D%22%22%20ownerpermit%3D%22%22%20rkey%3D%22D77766EC-3733-4BF1-99B4-003EE8E8106C%22%20usercat%3D%22241%22%3E%0A%20%20%3Cmember%20name%3D%22list%22%20type%3D%22list%22%20pageno%3D%223%22%20perpage%3D%2220%22%20request%3D%22catname%22%20order%3D%22id%20desc%22%20%2F%3E%0A%20%20%3Cmember%20name%3D%22paging%22%20type%3D%22list%22%20request%3D%22paging%22%20count%3D%225%22%20parentname%3D%22list%22%20%2F%3E%0A%20%20%3Cmember%20name%3D%22count%22%20type%3D%22scalar%22%20request%3D%22count%22%20%2F%3E%0A%3C%2Fbasis%3E&dmnid=20"
        },
        "cms": {
            "date": "10/20/2021",
            "time": "21:23",
            "date2": "20211020",
            "time2": "212317",
            "date3": "2021.10.20"
        },
        "form": {
            "command": "<basis core=\"dbsource\" source=\"basiscore\" mid=\"20\" name=\"db\" lid=\"1\" userid=\"122503\" ownerid=\"8044\" gid=\"\" catid=\"\" q=\"\" dmnid=\"\" ownerpermit=\"\" rkey=\"D77766EC-3733-4BF1-99B4-003EE8E8106C\" usercat=\"241\">\n  <member name=\"list\" type=\"list\" pageno=\"3\" perpage=\"20\" request=\"catname\" order=\"id desc\" />\n  <member name=\"paging\" type=\"list\" request=\"paging\" count=\"5\" parentname=\"list\" />\n  <member name=\"count\" type=\"scalar\" request=\"count\" />\n</basis>",
            "dmnid": "20"
        }
    }
}

source_context = ClientSourceContext(p["cms"], options)
result = app.dispatch(source_context)
print(result)
