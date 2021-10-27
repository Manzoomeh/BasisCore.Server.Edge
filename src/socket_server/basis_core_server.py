import json
from context import SourceContext
from socket_server import EndPoint, Server
from decorator import dispatch_context


class BasisCoreServer(Server):
    def __init__(self, ip: str, port: int):
        super().__init__(EndPoint(ip, port), BasisCoreServer.on_message_receive)

    @staticmethod
    def on_message_receive(request_bytes: list):
        request_str = request_bytes.decode("utf-8")
        request_object = json.loads(request_str)
        req = request_object["cms"]["request"]
        log = "{0} {1} {2}".format(
            req["request-id"], req["methode"], req["full-url"])
        print(log)

        context = SourceContext(request_object["cms"])
        # print(context)
        result = dispatch_context(context)
        # print(result)

        request_object["cms"]["content"] = json.dumps(result)
        request_object["cms"]["webserver"] = {
            "index": "5",
            "headercode": "200 Ok",
            "mime": "application/json"
        }
        request_object["cms"]["http"] = {"Access-Control-Allow-Headers": " *"}

        return json.dumps(request_object).encode("utf-8")
