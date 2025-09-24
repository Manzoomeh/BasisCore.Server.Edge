import re
from struct import error
from typing import Callable, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.logger import ILogger
from bclib.utility import DictEx
from bclib.context.client_source_context import ClientSourceContext
from bclib.context.context import Context
from bclib.context.restful_context import RESTfulContext
from bclib.context.web_context import WebContext
from bclib.context.request_context import RequestContext
from bclib.context.socket_context import SocketContext
from bclib.context.server_source_context import ServerSourceContext
from bclib.context.end_point_context import EndPointContext
from bclib.listener.message import Message, MessageType
from bclib.listener.http_listener.http_base_data_type import HttpBaseDataType


class ContextFactory:
    def __init__(self, options: 'DictEx', logger: 'ILogger'):
        self.logger = logger
        self.__default_router = options.defaultRouter\
            if 'defaultRouter' in options and isinstance(options.defaultRouter, str)\
            else None
        if options.has('router'):
            router = options.router
            if isinstance(router, str):
                self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
            elif isinstance(router, DictEx):
                self.__init_router_lookup(options.router)
            else:
                raise error(
                    "Invalid value for 'router' property in host options! Use string or dict object only.")
        elif self.__default_router:
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: self.__default_router
        else:
            raise error(
                "Invalid routing config! Please at least set one of 'router' or 'defaultRouter' property in host options.")

    def __init_router_lookup(self, router: 'DictEx'):
        """create router lookup dictionary"""

        route_dict = dict()
        for key, values in router.items():
            key = key.strip()
            if key != 'rabbit':
                if '*' in values:
                    route_dict['*'] = key
                    break
                else:
                    for value in values:
                        if len(value.strip()) != 0 and value not in route_dict:
                            route_dict[value] = key
        if len(route_dict) == 1 and '*' in route_dict and self.__default_router is None:
            router = route_dict['*']
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
        else:
            self.__context_type_lookup = route_dict.items()
            self.__context_type_detector = self.__context_type_detect_from_lookup

    def __context_type_detect_from_lookup(self, url: str) -> str:
        """Detect context type from url about lookup"""

        context_type: Optional[str] = None
        if url:
            try:
                for pattern, lookup_context_type in self.__context_type_lookup:
                    if pattern == "*" or re.search(pattern, url):
                        context_type = lookup_context_type
                        break
            except TypeError:
                pass
            except error as ex:
                print("Error in detect context from routing options!", ex)
        return context_type if context_type else self.__default_router

    async def create_context_async(self, message: 'Message', dispatcher: 'IDispatcher') -> Context:
        """Create context from message object"""

        message_json: dict = await message.get_json_async()

        ret_val: RequestContext = None
        context_type = None
        cms_object: Optional[dict] = None
        url: Optional[str] = None
        request_id: Optional[str] = None
        method: Optional[str] = None

        cms_object = message_json[HttpBaseDataType.CMS] if HttpBaseDataType.CMS in message_json else None
        if cms_object:
            if 'request' in cms_object:
                req = cms_object["request"]
            else:
                raise KeyError("request key not found in cms object")
            if 'full-url' in req:
                url = req["full-url"]
            else:
                raise KeyError("full-url key not found in request")
            request_id = req['request-id'] if 'request-id' in req else 'none'
            method = req['methode'] if 'methode' in req else 'none'
        if message.type == MessageType.AD_HOC:
            if url or self.__default_router is None:
                context_type = self.__context_type_detector(url)
            else:
                context_type = self.__default_router
        else:
            context_type = "endpoint"
        self.logger.log_request(
            f"({context_type}::{message.type.name}){f' - {request_id} {method} {url} ' if cms_object else ''}")

        if context_type == "client_source":
            ret_val = ClientSourceContext(cms_object, dispatcher, message)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms_object, dispatcher, message)
        elif context_type == "server_source":
            ret_val = ServerSourceContext(message_json, dispatcher)
        elif context_type == "web":
            ret_val = WebContext(cms_object, dispatcher, message)
        elif context_type == "endpoint":
            ret_val = EndPointContext(cms_object, dispatcher, message, message_json)
        elif context_type == "socket":
            ret_val = SocketContext(
                cms_object, dispatcher, message, message_json)
        elif context_type is None:
            raise NameError(f"No context found for '{url}'")
        else:
            raise NameError(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val