import json
import re
import asyncio
from typing import Any
from listener import EndPoint, SocketListener
from context import SourceContext, RESTfulContext, WebContext, RequestContext
from .dispatcher import Dispatcher


class SocketDispatcher(Dispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = SocketListener(
            EndPoint(options["ip"], options["port"]), self.__on_message_receive)

    def __on_message_receive(self, request_bytes: list) -> bytes:
        request_str = request_bytes.decode("utf-8")
        request_object = json.loads(request_str)
        req = request_object["cms"]["request"]
        log = "%s %s %s" % (
            req["request-id"], req["methode"], req["full-url"])
        print(log)
        context = self.__context_factory(
            req["full-url"], request_object["cms"], self._options)
        result = self.dispatch(context)
        response_object = context.generate_responce(result)
        return json.dumps(response_object).encode("utf-8")

    def __context_factory(self, url, *args: (Any)) -> RequestContext:
        ret_val: RequestContext = None
        context_type = None
        for key, patterns in self._options["router"].items():
            for pattern in patterns:
                if pattern == "*" or re.search(pattern, url):
                    context_type = key
                    break
            if context_type is not None:
                break
        if context_type == "dbsource":
            ret_val = SourceContext(*args)
        elif context_type == "restful":
            ret_val = RESTfulContext(*args)
        elif context_type == "web":
            ret_val = WebContext(*args)
        elif context_type is None:
            raise Exception("No context found for '%s'" % url)
        else:
            raise Exception(
                "Configured context type '%s' not found for '%s'" % (context_type, url))
        return ret_val

    def listening(self):
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')

    def start_listening(self):
        return self.__listener.process_async()
