import asyncio
import json
from socket_server import EndPoint, Server


def on_message_receive(request_bytes: list):
    request_str = request_bytes.decode("utf-8")
    request_object = json.loads(request_str)
    reqObj = request_object["cms"]["request"]
    log = "{0} {1} {2}".format(
        reqObj["request-id"], reqObj["methode"], reqObj["full-url"])
    print(log)

    request_object["cms"]["content"] = "{\"setting\": {\"keepalive\": true}, \"sources\": [{\"options\": {\"TabelName\": \"db.list\", \"keyFieldName\": null, \"statusFieldName\": null, \"mergeType\": 0}, \"data\": [{\"sta\": \"no\", \"page\": 1}, {\"sta\": \"no\", \"page\": 2}, {\"sta\": \"no\", \"page\": 3}, {\"sta\": \"no\", \"page\": 4}]}, {\"options\": {\"TabelName\": \"db.paging\", \"keyFieldName\": null, \"statusFieldName\": null, \"mergeType\": 0}, \"data\": [{\"count\": 72}]}]}"
    request_object["cms"]["webserver"] = {
        "index": "5",
        "headercode": "200 Ok",
        "mime": "application/json"
    }
    request_object["cms"]["http"] = {"Access-Control-Allow-Headers": " *"}

    return json.dumps(request_object).encode("utf-8")


async def main():
    receiver = EndPoint('127.0.0.1', 1025)
    server = Server(receiver, on_message_receive)
    await server.process_async()


asyncio.run(main())
