import json
import asyncio
from listener import EndPoint, SocketListener
from context import SourceContext
from .dispatcher import Dispatcher


class SocketDispatcher(Dispatcher):
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.__listener = SocketListener(
            EndPoint(ip, port), self.__on_message_receive)

    def __on_message_receive(self, request_bytes: list) -> bytes:
        request_str = request_bytes.decode("utf-8")
        request_object = json.loads(request_str)
        req = request_object["cms"]["request"]
        log = "{0} {1} {2}".format(
            req["request-id"], req["methode"], req["full-url"])
        print(log)

        context = SourceContext(request_object["cms"])
        result = self.dispatch(context)

        request_object["cms"]["content"] = json.dumps(result)
        request_object["cms"]["webserver"] = {
            "index": "5",
            "headercode": "200 Ok",
            "mime": "application/json"
        }
        request_object["cms"]["http"] = {"Access-Control-Allow-Headers": " *"}

        return json.dumps(request_object).encode("utf-8")

    def listening(self):
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')

    def start_listening(self):
        return self.__listener.process_async()
