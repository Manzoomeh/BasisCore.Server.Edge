from abc import abstractmethod
import json
import re
from context import SourceContext, RESTfulContext, WebContext, RequestContext
from context import Context
from context import SocketContext
from listener import Message, MessageType
from .dispatcher import Dispatcher


class RoutingDispatcher(Dispatcher):
    def __init__(self, options: dict):
        super().__init__(options)

    def _on_message_receive(self, message: Message) -> Message:
        context = self.__context_factory(message)
        result = self.dispatch(context)
        ret_val: Message = None
        if isinstance(context, RequestContext):
            response = context.generate_responce(result)
            if context.response is not None:
                for key, value in context.response["cms"].items():
                    if key not in response:
                        response[key] = dict()
                    response[key].update(value)
            message_result = json.dumps(response).encode("utf-8")
            ret_val = Message.create_add_hock(
                message.session_id, message_result)
            self._send_message(ret_val)
        return ret_val

    def __context_factory(self, message: Message) -> Context:
        """Create context from message object"""

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

    @abstractmethod
    def _send_message(self, message: Message) -> None:
        """Send message to endpoint"""

    def listening(self):
        super().listening()
