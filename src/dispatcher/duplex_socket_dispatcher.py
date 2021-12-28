import json
import re
import asyncio
from context import SourceContext, RESTfulContext, WebContext, RequestContext
from listener import EndPoint, DuplexSocketListener, Message
from .dispatcher import Dispatcher


class DuplexSocketDispatcher(Dispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = DuplexSocketListener(
            EndPoint(self.options.receiver.ip, self.options.receiver.port),
            EndPoint(self.options.sender.ip, self.options.sender.port),
            self.__on_message_receive)

    def __on_message_receive(self, message: Message) -> None:
        request_str = message.buffer.decode("utf-8")
        request_object = json.loads(request_str)
        req = request_object["cms"]["request"]
        log = f"{req['request-id']} {req['methode']} {req['full-url']}"
        print(log)
        context = self.__context_factory(
            req["full-url"], request_object["cms"])
        result = self.dispatch(context)

        response = context.generate_responce(result)
        if context.response is not None:
            for key, value in context.response["cms"].items():
                if key not in response:
                    response[key] = dict()
                response[key].update(value)
        message_result = json.dumps(response).encode("utf-8")
        new_message = Message.create_add_hock(
            message.session_id, message_result)
        self.__listener.send_message(new_message)

    def __context_factory(self, url, cms_request: dict) -> RequestContext:
        ret_val: RequestContext = None
        context_type = None
        for key, patterns in self._options["router"].items():
            if key != "rabbit":
                for pattern in patterns:
                    if pattern == "*" or re.search(pattern, url):
                        context_type = key
                        break
            if context_type is not None:
                break
        if context_type == "dbsource":
            ret_val = SourceContext(cms_request, self)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms_request, self)
        elif context_type == "web":
            ret_val = WebContext(cms_request, self)
        elif context_type is None:
            raise Exception(f"No context found for '{url}'")
        else:
            raise Exception(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')

    def start_listening(self):
        return self.__listener.process_async()
