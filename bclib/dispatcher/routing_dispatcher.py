import json
import re
from struct import error
from typing import Callable

from bclib.utility.dict_ex import DictEx

from bclib.context import ClientSourceContext, RESTfulContext, WebContext, RequestContext, Context, SocketContext, ServerSourceContext
from bclib.listener import Message, MessageType, HttpBaseDataType
from ..dispatcher.dispatcher import Dispatcher


class RoutingDispatcher(Dispatcher):

    def __init__(self, options: dict):
        super().__init__(options)
        self.__default_router = self.options.defaultRouter\
            if 'defaultRouter' in self.options and isinstance(self.options.defaultRouter, str)\
            else None

        if 'router' in self.options:
            router = self.options["router"]
            if isinstance(router, str):
                self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
            elif isinstance(router, DictEx):
                self.init_router_lookup()
            else:
                raise error(
                    "Invalid value for 'router' property in host options! Use string or dict object only.")
        elif self.__default_router:
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: self.__default_router
        else:
            raise error(
                "Invalid routing config! Please at least set one of 'router' or 'defaultRouter' property in host options.")

    def init_router_lookup(self):
        """create router lookup dictionary"""

        route_dict = dict()
        for key, values in self.options["router"].items():
            if key != 'rabbit'.strip():
                if '*' in values:
                    route_dict['*'] = key
                    break
                else:
                    for value in values:
                        if len(value.strip()) != 0 and value not in route_dict:
                            route_dict[value] = key
        if len(route_dict) == 1 and '*' in route_dict:
            router = route_dict['*']
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
        else:
            self.__context_type_lookup = route_dict.items()
            self.__context_type_detector = self.__context_type_detect_from_lookup

    def __context_type_detect_from_lookup(self, url: str) -> str:
        """Detect context type from url about lookup"""

        context_type: str = None
        if url:
            try:
                for pattern, lookup_conyext_type in self.__context_type_lookup:
                    if pattern == "*" or re.search(pattern, url):
                        context_type = lookup_conyext_type
                        break
            except TypeError:
                pass
            except error as ex:
                print("Error in detect context from routing options!", ex)
        return context_type if context_type else self.__default_router

    def _on_message_receive(self, message: Message) -> Message:
        """Process received message"""

        try:
            context = self.__context_factory(message)
            response = self.dispatch(context)
            ret_val: Message = None
            if context.is_adhoc:
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

        if context_type == "client_source":
            ret_val = ClientSourceContext(cms_object, self)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms_object, self)
        elif context_type == "server_source":
            ret_val = ServerSourceContext(message_json, self)
        elif context_type == "web":
            ret_val = WebContext(cms_object, self)
        elif context_type == "socket":
            ret_val = SocketContext(cms_object, self, message, message_json)
        elif context_type is None:
            raise Exception(f"No context found for '{url}'")
        else:
            raise Exception(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val
