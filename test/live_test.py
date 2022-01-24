import json
from pathlib import Path
from context.web_context import WebContext
from dispatcher import SocketDispatcher
from context import ClientSourceContext, ClientSourceMemberContext, RESTfulContext


with open(Path(__file__).with_name("host.json"), encoding='UTF-8') as options_file:
    options = json.load(options_file)

app = SocketDispatcher(options)


# @app.web_action(
#     app.url("py/app/d"))
# def process_basiscore_web3(_: WebContext):
#     print("process_basiscore_restful1")
#     return "<h1>Hello world!</h1>dddd"


# @app.web_action(
#     app.url("py/:type/qam/:id"),
#     app.in_list("context.url_segments.type", "book", "car"))
# def process_basiscore_web2(context: WebContext):
#     print("process_basiscore_restful1")
#     return "<h1>Hello world!</h1>id is :{0}<br/> type is:{1}</br/".format(context.url_segments.id, context.url_segments.type)


# @app.web_action(
#     app.url("py/:rkey"))
# def process_basiscore_web1(context: WebContext):
#     print("process_basiscore_restful1")
#     return "<h1>Hello world! / </h1> rkey is :" + context.url_segments.rkey

@app.web_action(app.url("xhr"))
def process_basiscore_web4(context: WebContext):
    return """
<script>
var data = JSON.stringify({
  "actions": [
    {
      "request": "add",
      "mid": "43",
      "productid": "794525",
      "count": "1"
    },
    {
      "request": "add",
      "mid": "43",
      "productid": "794520",
      "count": "2"
    }
  ]
});

var xhr = new XMLHttpRequest();

xhr.addEventListener("readystatechange", function () {
  if (this.readyState === 4) {
    console.log(this.responseText);
  }
});

xhr.open("POST", "rest/create-factor/B0B03E47-2FA7-4D97-AF2E-642D9B5D5FF5");
xhr.setRequestHeader("content-type", "application/json");

xhr.send(data);
</script>
"""


@app.web_action(app.url("fetch"))
def process_basiscore_web46(context: WebContext):
    return """
    <script>
var data = JSON.stringify({
  "actions": [
    {
      "request": "add",
      "mid": "43",
      "productid": "794525",
      "count": "1"
    },
    {
      "request": "add",
      "mid": "43",
      "productid": "794520",
      "count": "2"
    }
  ]
});
fetch("rest/create-factor/B0B03E47-2FA7-4D97-AF2E-642D9B5D5FF5", {
  method: 'post',
   headers: {
    'Content-Type': 'application/json'
  },
  body: data
}).then(response => response.json())
  .then(data => console.log(data));
</script>
"""


@app.web_action(app.url("fetch2"))
def process_basiscore_web45(context: WebContext):
    context.add_header("Access-Control-Allow-Origin", "*")
    return """
    <script>
var myHeaders = new Headers();
myHeaders.append("Content-Type", "application/json");
myHeaders.append("Access-Control-Allow-Origin","*");

var raw = JSON.stringify({"actions":[{"request":"add","mid":"43","productid":"794525","count":"1"}]});

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'follow'
};

fetch("https://basisfly.com/rest/create-factor/A2E02B5B-6D89-4B0C-8ACF-75712B3D8E67", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
</script>
"""


@app.web_action()
def process_basiscore_web44(context: WebContext):
    return """
    <html><head></head><body>
     <iframe  id="frame" ></iframe> 
<form method="post"  action="rest/create-factor/B0B03E47-2FA7-4D97-AF2E-642D9B5D5FF5" target="frame">
<input type="text" value="hi qam" name="data"/>
 <input type="text" value='{"actions":[{"request":"add","mid":"43","productid":"794525","count":"1"},{"request":"add","mid":"43","productid":"794520","count":"2"}]}' name="create_factor_json"/>
 <input type="submit" value="send"/>
</form>
</body><html>
"""


@app.restful_action(app.url("rest/create-factor/:rkey"))
def process_basiscore_restful1(context: RESTfulContext):
    print("restful_action")
    ret_val = dict()
    ret_val["client"] = context.body
    ret_val["rkey"] = context.url_segments
    ret_val["message"] = "hello world!10"
    return ret_val


# @app.web_action(app.url("tt/:rkey/:*pp"))
# def process_basiscore_web4(context: WebContext):
#     print("process_basiscore_restful1")
#     # context.response = {
#     #     "cms": {
#     #         "cms": {
#     #             "webserver": {
#     #                 "index": "1"
#     #             }
#     #         }
#     #     }
#     # }
#     print(context.url_segments)
#     return "<h1>Hello world! [##cms.cms.time##]{0}</h1>".format(context.url_segments.rkey)
#     # return '''<Basis core="component.local.ListOfChoices" run="atclient" inventorysource="db.anbar"
#     # 					localstoragesource="local.basket" basket-result-id="db.Listchoices" ></Basis>'''


# @app.restful_action(
#     app.in_list("context.body.id", 10))
# def process_basiscore_restful1(context: RESTfulContext):
#     ret_val = dict()
#     ret_val["client"] = context.body
#     ret_val["message"] = "hello world!10"
#     return ret_val


# @app.restful_action(
#     app.in_list("context.body.id", 12),
#     app.equal("context.body.age", 13))
# def process_basiscore_restful2(context: RESTfulContext):
#     ret_val = dict()
#     ret_val["client"] = context.body
#     ret_val["message"] = "hello world!12-age"
#     return ret_val


# @app.restful_action(
#     app.in_list("context.body.id", 12))
# def process_basiscore_restful3(context: RESTfulContext):
#     ret_val = dict()
#     ret_val["client"] = context.body
#     ret_val["message"] = "hello world!12"
#     return ret_val


# @app.restful_action()
# def process_basiscore_restful4(_: RESTfulContext):
#     ret_val = dict()
#     ret_val["message"] = "hello world! - No match"
#     return ret_val


# @app.source_action(
#     app.equal("context.command.source", "basiscore"),
#     app.in_list("context.command.mid", "10", "20"))
# def process_basiscore_source(context: SourceContext):
#     print("process1 ",  context)
#     context.response = {
#         "cms": {
#             "cms": {
#                 "http": {
#                     "Access-Control-Allow-Headers": " *",
#                     "x-extra-data": "12"
#                 }
#             }
#         }
#     }
#     data = [
#         {"id": 1, "name": "Data1"},
#         {"id": 2, "name": "Data2"},
#         {"id": 3, "name": "Data3"},
#         {"id": 4, "name": "Data4"}
#     ]
#     return data


# @app.source_action(
#     app.equal("context.command.source", "demo"),
#     app.in_list("context.command.mid", "10", "20"))
# def process_demo_source(context: SourceContext):
#     print("process1 ",  context)

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

    # data = [
    #     {"id": 44, "name": "Data 44", "age": 22},
    #     {"id": 66, "name": "Data 66", "age": 50},
    #     {"id": 76, "name": "Data 76", "age": 30},
    #     {"id": 89, "name": "Data 89", "age": 52},
    #     {"id": 70, "name": "Data 70", "age": 37},
    #     {"id": 40, "name": "Data 40", "age": 45}
    # ]
    # return data


# @app.source_member_action(
#     app.equal("context.member.name", "list")
# )
# # @app.cache(key="member-list")
# def process_list_member(context: SourceMemberContext):
#     print("process_list_member")
#     return context.data


# @app.source_member_action(
#     app.equal("context.member.name", "paging")
# )
# # @app.cache(10)
# def process_page_member(context: SourceMemberContext):
#     data = {
#         "total": len(context.data),
#         "from": 0,
#         "to": len(context.data)-1,
#     }
#     print("process_page_member")
#     return data


# @app.source_member_action(
#     app.equal("context.member.name", "count")
# )
# def process_count_member(context: SourceMemberContext):
#     data = {
#         "count": len(context.data)
#     }
#     print("process_count_member")
#     return data


# @app.source_member_action()
# def all_member_process(_: SourceMemberContext):
#     print("all_member_process", )
#     return None


app.listening()
