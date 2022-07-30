import asyncio
import inspect
import json
import re
from struct import error
from typing import Callable, Any, Coroutine
from abc import abstractmethod

from bclib.utility import DictEx

from bclib.context import ClientSourceContext, RESTfulContext, WebContext, RequestContext, Context, SocketContext, ServerSourceContext, NamedPipeContext
from bclib.listener import Message, MessageType, HttpBaseDataType

from ..dispatcher.dispatcher_helper import DispatcherHelper
from ..dispatcher.dispatcher import Dispatcher


class RoutingDispatcher(Dispatcher, DispatcherHelper):

    def __init__(self, options: dict):
        super().__init__(options)
        self.__default_router = self.options.defaultRouter\
            if 'defaultRouter' in self.options and isinstance(self.options.defaultRouter, str)\
            else None
        self.name = self.options["name"] if self.options.has("name") else None
        self.__log_name = f"{self.name}: " if self.name else ''
        if self.options.has('router'):
            router = self.options.router
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
        for key, values in self.options.router.items():
            if key != 'rabbit'.strip():
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

        context_type: str = None
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

    async def _on_message_receive_async(self, message: Message) -> Message:
        """Process received message"""

        try:
            context = self.__context_factory(message)
            response = await self.dispatch_async(context)
            ret_val: Message = None
            if context.is_adhoc:
                message_result = json.dumps(response).encode("utf-8")
                ret_val = Message.create_add_hock(
                    message.session_id, message_result)
                await self.send_message_async(ret_val)
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
        if message.type == MessageType.AD_HOC:
            if url or self.__default_router is None:
                context_type = self.__context_type_detector(url)
            else:
                context_type = self.__default_router
        else:
            context_type = "socket"
        if self.log_request:
            print(
                f"{self.__log_name}({context_type}::{message.type.name}){f' - {request_id} {method} {url} ' if cms_object else ''}")

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
        elif context_type == "named_pipe":
            ret_val = NamedPipeContext(message_json, message_string, self)
        elif context_type is None:
            raise Exception(f"No context found for '{url}'")
        else:
            raise Exception(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val

    def run_in_background(self, callback: 'Callable|Coroutine', *args: Any) -> asyncio.Future:
        """helper for run function in background thread"""

        if inspect.iscoroutinefunction(callback):
            return self.event_loop.create_task(callback(*args))
        else:
            return self.event_loop.run_in_executor(None, callback, *args)

    @abstractmethod
    async def send_message_async(self, message: MessageType) -> bool:
        """Send message to endpoint"""

    def cache(self, seconds: int = 0, key: str = None):
        """Cache result of function for seconds of time or until signal by key for clear"""

        return self.cache_manager.cache_decorator(seconds, key)
