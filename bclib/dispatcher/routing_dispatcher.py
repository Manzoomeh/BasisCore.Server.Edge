from abc import abstractmethod
import json
import re
from struct import error
from bclib.context import SourceContext, RESTfulContext, WebContext, RequestContext, Context, SocketContext
from bclib.listener import Message, MessageType
from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType
from ..dispatcher.dispatcher import Dispatcher


class RoutingDispatcher(Dispatcher):

    def __init__(self, options: dict):
        super().__init__(options)

    def _on_message_receive(self, message: Message) -> Message:
        """Process received message"""

        try:
            context = self.__context_factory(message)
            result = self.dispatch(context)
            ret_val: Message = None
            if isinstance(context, RequestContext):
                response = context.generate_responce(result)
                message_result = json.dumps(response).encode("utf-8")
                ret_val = Message.create_add_hock(
                    message.session_id, message_result)
                self._send_message(ret_val)
            return ret_val
        except error as ex:
            print(f"Error in process received message {ex}")
            raise ex

    def __context_factory(self, message: Message) -> Context:
        """Create context from message object"""

        ret_val: RequestContext = None
        context_type = None
        cms: dict = None
        url: str = None
        request_id: str = None
        method: str = None
        if message.buffer:
            message_params = json.loads(message.buffer.decode("utf-8"))
            cms = message_params[HttpBaseDataType.CMS]
            req = cms["request"]
            request_id = req['request-id']
            method = req['methode']
            url = req["full-url"]
            meta = cms["_meta"] if "_meta" in cms else None
            if meta is not None and "context_type" in meta:
                context_type = meta["context_type"]
            else:
                if message.type == MessageType.AD_HOC:
                    for key, patterns in self.options["router"].items():
                        if key != "rabbit":
                            for pattern in patterns:
                                if pattern == "*" or re.search(pattern, url):
                                    context_type = key
                                    break
                        if context_type is not None:
                            break
                else:
                    context_type = "socket"

        print(f"{request_id} {method} {url} ({context_type})")

        if context_type == "dbsource":
            ret_val = SourceContext(cms, self)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms, self)
        elif context_type == "web":
            ret_val = WebContext(cms, self)
        elif context_type == "socket":
            ret_val = SocketContext(cms, self, message)
        elif context_type is None:
            raise Exception(f"No context found for '{url}'")
        else:
            raise Exception(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val

    @abstractmethod
    def _send_message(self, message: Message) -> bool:
        """Send message to endpoint"""
