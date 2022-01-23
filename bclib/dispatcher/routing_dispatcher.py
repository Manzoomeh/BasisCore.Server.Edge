from abc import abstractmethod
import json
import re
from struct import error
from typing import Callable

from bclib.context import SourceContext, RESTfulContext, WebContext, RequestContext, Context, SocketContext, ServerSourceContext
from bclib.listener import Message, MessageType, HttpBaseDataType
from ..dispatcher.dispatcher import Dispatcher


class RoutingDispatcher(Dispatcher):

    def __init__(self, options: dict):
        super().__init__(options)
        router = self.options["router"]
        if isinstance(router, str):
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
        else:
            self.__context_type_lookup = self.options["router"].items()
            self.__context_type_detector = self.__context_type_detect_from_lookup

    def __context_type_detect_from_lookup(self, url: str) -> str:
        """Detect context type from url about lookup"""

        context_type: str = None
        for key, patterns in self.__context_type_lookup:
            if key != "rabbit":
                for pattern in patterns:
                    if pattern == "*" or re.search(pattern, url):
                        context_type = key
                        break
            if context_type is not None:
                break
        return context_type

    def _on_message_receive(self, message: Message) -> Message:
        """Process received message"""

        try:
            context = self.__context_factory(message)
            result = self.dispatch(context)
            ret_val: Message = None
            if context.is_adhoc:
                response = context.generate_responce(result)
                message_result = json.dumps(response).encode("utf-8")
                ret_val = Message.create_add_hock(
                    message.session_id, message_result)
                self.send_message(ret_val)
            return ret_val
        except error as ex:
            print(f"Error in process received message {ex}")
            raise ex

    def __context_factory(self, message: Message) -> Context:
        """Create context from message object"""

        ret_val: RequestContext = None
        context_type = None
        cms_object: dict = None
        url: str = None
        request_id: str = None
        method: str = None
        message_json: dict = None
        if message.buffer:
            message_string = message.buffer.decode("utf-8")
            message_json = json.loads(message_string)
            cms_object = message_json[HttpBaseDataType.CMS] if HttpBaseDataType.CMS in message_json else None
            if cms_object:
                req = cms_object["request"]
                request_id = req['request-id']
                method = req['methode']
                url = req["full-url"]
        context_type = self.__context_type_detector(
            url) if message.type == MessageType.AD_HOC else "socket"

        print(
            f"({context_type}::{message.type.name}){f' : {request_id} {method} {url} ' if cms_object else ''}")

        if context_type == "dbsource":
            ret_val = SourceContext(cms_object, self)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms_object, self)
        elif context_type == "web":
            ret_val = WebContext(cms_object, self)
        elif context_type == "socket":
            ret_val = SocketContext(cms_object, self, message, message_json)
        elif context_type == "server_dbsource":
            ret_val = ServerSourceContext(message_json, self)
        elif context_type is None:
            raise Exception(f"No context found for '{url}'")
        else:
            raise Exception(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val
