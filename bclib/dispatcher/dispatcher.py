"""Base class for dispaching request"""
import asyncio
import inspect
from abc import ABC
from typing import Callable, Any
from functools import wraps

from bclib.logger import ILogger, LoggerFactory
from bclib.cache import create_chaching
from bclib.listener import RabbitBusListener
from bclib.predicate import Predicate
from bclib.context import ClientSourceContext, ClientSourceMemberContext, WebContext, Context, RESTfulContext, RabbitContext, SocketContext, ServerSourceContext, ServerSourceMemberContext
from bclib.db_manager import DbManager
from bclib.utility import DictEx
from bclib.exception import HandlerNotFoundErr
from ..dispatcher.callback_info import CallbackInfo


class Dispatcher(ABC):
    """Base class for dispaching request"""

    def __init__(self, options: dict = None):
        self.options = DictEx(options)
        self.__look_up: 'dict[str, list[CallbackInfo]]' = dict()
        cache_options = self.options.cache if "cache" in self.options else None
        self.cache_manager = create_chaching(cache_options)
        self.db_manager = DbManager(self.options)
        self.__logger: ILogger = LoggerFactory.create(self.options)
        self.__rabbit_dispatcher: 'list[RabbitBusListener]' = list()
        if "router" in self.options and "rabbit" in self.options.router:
            for setting in self.options.router.rabbit:
                self.__rabbit_dispatcher.append(
                    RabbitBusListener(setting, self))

    def socket_action(self, * predicates: (Predicate)):
        """Decorator for determine Socket action"""

        def _decorator(socket_action_handler: 'Callable[[SocketContext],bool]'):

            @wraps(socket_action_handler)
            async def non_async_wrapper(context: SocketContext):
                return socket_action_handler(context)

            @wraps(socket_action_handler)
            async def async_wrapper(context: SocketContext):
                return await socket_action_handler(context)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                socket_action_handler) else non_async_wrapper

            self._get_context_lookup(SocketContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return socket_action_handler
        return _decorator

    def restful_action(self, * predicates: (Predicate)):
        """Decorator for determine RESTful action"""

        def _decorator(restful_action_handler: 'Callable[[RESTfulContext], dict]'):

            @wraps(restful_action_handler)
            async def non_async_wrapper(context: RESTfulContext):
                return context.generate_responce(restful_action_handler(context))

            @wraps(restful_action_handler)
            async def async_wrapper(context: RESTfulContext):
                return context.generate_responce(await restful_action_handler(context))

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                restful_action_handler) else non_async_wrapper

            self._get_context_lookup(RESTfulContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return restful_action_handler
        return _decorator

    def web_action(self, * predicates: (Predicate)):
        """Decorator for determine legacy web request action"""

        def _decorator(web_action_handler: 'Callable[[WebContext], str]'):

            @wraps(web_action_handler)
            async def non_async_wrapper(context: WebContext):
                return context.generate_responce(web_action_handler(context))

            @wraps(web_action_handler)
            async def async_wrapper(context: WebContext):
                return context.generate_responce(await web_action_handler(context))

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                web_action_handler) else non_async_wrapper

            self._get_context_lookup(WebContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return web_action_handler
        return _decorator

    def client_source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action"""

        def _decorator(client_source_action_handler: 'Callable[[ClientSourceContext], Any]'):
            @wraps(client_source_action_handler)
            async def non_async_wrapper(context: ClientSourceContext):
                data = client_source_action_handler(context)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = ClientSourceMemberContext(
                            context, data, member)
                        dispath_result = await self.dispatch_async(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value
                            },
                            "data": dispath_result
                        }
                        result_set.append(result)
                ret_val = {
                    "setting": {
                        "keepalive": False,
                    },
                    "sources": result_set
                }
                return context.generate_responce(ret_val)

            @wraps(client_source_action_handler)
            async def async_wrapper(context: ClientSourceContext):
                data = await client_source_action_handler(context)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = ClientSourceMemberContext(
                            context, data, member)
                        dispath_result = await self.dispatch_async(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value
                            },
                            "data": dispath_result
                        }
                        result_set.append(result)
                ret_val = {
                    "setting": {
                        "keepalive": False,
                    },
                    "sources": result_set
                }
                return context.generate_responce(ret_val)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                client_source_action_handler) else non_async_wrapper

            self._get_context_lookup(ClientSourceContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))

            return client_source_action_handler
        return _decorator

    def client_source_member_action(self, *predicates: (Predicate)):
        """Decorator for determine source member action methode"""

        def _decorator(client_source_member_handler: 'Callable[[ClientSourceMemberContext], Any]'):

            @wraps(client_source_member_handler)
            async def non_async_wrapper(context: WebContext):
                return client_source_member_handler(context)

            @wraps(client_source_member_handler)
            async def async_wrapper(context: WebContext):
                return await client_source_member_handler(context)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                client_source_member_handler) else non_async_wrapper

            self._get_context_lookup(ClientSourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return client_source_member_handler
        return _decorator

    def server_source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action"""

        def _decorator(server_source_action_handler: 'Callable[[ServerSourceContext], Any]'):
            @wraps(server_source_action_handler)
            async def non_async_wrapper(context: ServerSourceContext):
                data = server_source_action_handler(context)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = ServerSourceMemberContext(
                            context, data, member)
                        dispath_result = await self.dispatch_async(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value
                            },
                            "data": dispath_result
                        }
                        result_set.append(result)
                ret_val = {
                    "setting": {
                        "keepalive": False,
                    },
                    "sources": result_set
                }
                return context.generate_responce(ret_val)

            @wraps(server_source_action_handler)
            async def async_wrapper(context: ServerSourceContext):
                data = await server_source_action_handler(context)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = ServerSourceMemberContext(
                            context, data, member)
                        dispath_result = await self.dispatch_async(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value
                            },
                            "data": dispath_result
                        }
                        result_set.append(result)
                ret_val = {
                    "setting": {
                        "keepalive": False,
                    },
                    "sources": result_set
                }
                return context.generate_responce(ret_val)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                server_source_action_handler) else non_async_wrapper

            self._get_context_lookup(ServerSourceContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))

            return server_source_action_handler
        return _decorator

    def server_source_member_action(self, *predicates: (Predicate)):
        """Decorator for determine server source member action methode"""

        def _decorator(server_source_member_action_handler: 'Callable[[ServerSourceMemberContext], Any]'):

            @wraps(server_source_member_action_handler)
            async def non_async_wrapper(context: WebContext):
                return server_source_member_action_handler(context)

            @wraps(server_source_member_action_handler)
            async def async_wrapper(context: WebContext):
                return await server_source_member_action_handler(context)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                server_source_member_action_handler) else non_async_wrapper

            self._get_context_lookup(ServerSourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return server_source_member_action_handler
        return _decorator

    def rabbit_action(self, * predicates: (Predicate)):
        """Decorator for determine rabbit-mq message request action"""

        def _decorator(rabbit_action_handler: 'Callable[[RabbitContext], bool]'):

            @wraps(rabbit_action_handler)
            async def non_async_wrapper(context: RabbitContext):
                return rabbit_action_handler(context)

            @wraps(rabbit_action_handler)
            async def async_wrapper(context: RabbitContext):
                return await rabbit_action_handler(context)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                rabbit_action_handler) else non_async_wrapper

            self._get_context_lookup(RabbitContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))

            return rabbit_action_handler
        return _decorator

    def _get_context_lookup(self, key: str) -> 'list[CallbackInfo]':
        """Get key related action list object"""

        ret_val: None
        if key in self.__look_up:
            ret_val = self.__look_up[key]
        else:
            ret_val = list()
            self.__look_up[key] = ret_val
        return ret_val

    async def dispatch_async(self, context: Context) -> Any:
        """Dispatch context and get result from related action methode"""

        result: Any = None
        name = type(context).__name__
        try:
            items = self._get_context_lookup(name)
            for item in items:
                result = await item.try_execute_async(context)
                if result is not None:
                    break
            else:
                result = context.generate_error_responce(
                    HandlerNotFoundErr(name))
        except Exception as ex:
            result = context.generate_error_responce(ex)
        return result

    def initialize_task(self, loop: asyncio.AbstractEventLoop):
        for dispacher in self.__rabbit_dispatcher:
            dispacher.initialize_task(loop)

    async def log_async(self, **kwargs):
        """log params bt internal precess"""
        await self.__logger.log_async(**kwargs)
