import json
import re
import asyncio
from context import SourceContext, RESTfulContext, WebContext, RequestContext
from context.context import Context
from context.socket_context import SocketContext
from listener import EndPoint, DuplexSocketListener, Message, MessageType
from .dispatcher import Dispatcher


class SocketDispatcher(Dispatcher):
    def __init__(self, options: dict):
        super().__init__(options)
        self.__listener = DuplexSocketListener(
            EndPoint(self.options.receiver.ip, self.options.receiver.port),
            EndPoint(self.options.sender.ip, self.options.sender.port),
            self.__on_message_receive)

    def __on_message_receive(self, message: Message) -> None:
        context = self.__context_factory(message)
        result = self.dispatch(context)
        # message.type == MessageType.AD_HOC:
        if isinstance(context, RequestContext):
            response = context.generate_responce(result)
            if context.response is not None:
                for key, value in context.response["cms"].items():
                    if key not in response:
                        response[key] = dict()
                    response[key].update(value)
            message_result = json.dumps(response).encode("utf-8")
            new_message = Message.create_add_hock(
                message.session_id, message_result)
            self.send_message(new_message)

    def __context_factory(self, message: Message) -> Context:
        ret_val: RequestContext = None
        context_type = None
        request: dict = None
        url: str = None
        if message.buffer:
            meaage_params = json.loads(message.buffer.decode("utf-8"))
            request = meaage_params["cms"]
            req = request["request"]
            url = req["full-url"]
            print(f"{req['request-id']} {req['methode']} {url}")
        if message.type == MessageType.AD_HOC:
            for key, patterns in self._options["router"].items():
                if key != "rabbit":
                    for pattern in patterns:
                        if pattern == "*" or re.search(pattern, url):
                            context_type = key
                            break
                if context_type is not None:
                    break
            if context_type == "dbsource":
                ret_val = SourceContext(request, self)
            elif context_type == "restful":
                ret_val = RESTfulContext(request, self)
            elif context_type == "web":
                ret_val = WebContext(request, self)
            elif context_type is None:
                raise Exception(f"No context found for '{url}'")
            else:
                raise Exception(
                    f"Configured context type '{context_type}' not found for '{url}'")
        else:
            ret_val = SocketContext(request, self, message)
        return ret_val

    def send_message(self, message: Message) -> None:
        """Send message to endpoint"""

        self.__listener.send_message(message)

    def listening(self):
        super().listening()
        try:
            asyncio.run(self.__listener.process_async())
        except KeyboardInterrupt:
            print('Bye!')

    def start_listening(self):
        return self.__listener.process_async()
