"""Base class for dispaching request"""
import asyncio
from typing import Callable, Any
from functools import wraps
from cache import create_chaching, CacheManager
from listener import RabbitBusListener
from predicate import Predicate, InList, Equal, Url, Between, NotEqual, GreaterThan, LessThan, LessThanEqual, GreaterThanEqual, Match, HasValue
from context import SourceContext, SourceMemberContext, WebContext, Context, RESTfulContext, RabbitContext
from utility import DictEx
from .callback_info import CallbackInfo


class Dispatcher:
    """Base class for dispaching request"""

    def __init__(self, options: dict = None):
        self._options = DictEx(options)
        self.__look_up: dict[str, list[CallbackInfo]] = dict()
        cache_options = self._options.cache if "cache" in self._options else None
        self.__cache_manager = create_chaching(cache_options)
        self.__rabbit_dispatcher: list[RabbitBusListener] = list()
        if "router" in self._options and "rabbit" in self._options.router:
            for setting in self._options.router.rabbit:
                self.__rabbit_dispatcher.append(
                    RabbitBusListener(setting, self._options, self.dispatch))
                print(setting)

        print("Version : 1.1.0")

    @property
    def options(self) -> DictEx:
        return self._options

    @property
    def cache_manager(self) -> CacheManager:
        return self.__cache_manager

    def restful_action(self, * predicates: (Predicate)):
        """Decorator for determine RESTful action"""

        def _decorator(restful_action: Callable[[RESTfulContext], list]):
            @wraps(restful_action)
            def _wrapper(context: RESTfulContext):
                return restful_action(context)
            self._get_context_lookup(RESTfulContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def web_action(self, * predicates: (Predicate)):
        """Decorator for determine legacy web request action"""

        def _decorator(web_action: Callable[[WebContext], list]):
            @wraps(web_action)
            def _wrapper(context: WebContext):
                return web_action(context)
            self._get_context_lookup(WebContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action"""

        def _decorator(source_action: Callable[[SourceContext], list]):
            @wraps(source_action)
            def _wrapper(context: SourceContext):
                data = source_action(context)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = SourceMemberContext(
                            context, data, member, self._options)
                        dispath_result = self.dispatch(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value[0]
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
                return ret_val
            self._get_context_lookup(SourceContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def source_member_action(self, *predicates: (Predicate)):
        """Decorator for determine source member action methode"""

        def _decorator(function: Callable[[SourceMemberContext], list]):

            @wraps(function)
            def _wrapper(context: SourceMemberContext):
                return function(context)

            self._get_context_lookup(SourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def rabbit_action(self, * predicates: (Predicate)):
        """Decorator for determine rabbit-mq message request action"""

        def _decorator(web_action: Callable[[RabbitContext], list]):
            @wraps(web_action)
            def _wrapper(context: RabbitContext):
                web_action(context)
                return True
            self._get_context_lookup(RabbitContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def _get_context_lookup(self, key: str) -> list[CallbackInfo]:
        """Get key related action list object"""

        ret_val: None
        if key in self.__look_up:
            ret_val = self.__look_up[key]
        else:
            ret_val = list()
            self.__look_up[key] = ret_val
        return ret_val

    def dispatch(self, context: Context) -> Any:
        """Dispatch context and get result from related action methode"""

        result: Any = None
        name = type(context).__name__
        items = self._get_context_lookup(name)
        for item in items:
            result = item.try_execute(context)
            if result is not None:
                break
        return result

    def listening(self):
        for dispacher in self.__rabbit_dispatcher:
            dispacher.start_listening()

    def run_in_background(self, callback: Callable, *args: Any) -> Any:
        """helper for run function in background thread"""

        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, callback, *args)

    def cache(self, seconds: int = 0, key: str = None):
        """Cache result of function for seconds of time or until signal by key for clear"""

        return self.__cache_manager.cache_decorator(seconds, key)

    def reset_cache(self, key: str):
        """Remove key related cache"""

        self.__cache_manager.reset_cache(key)

    @staticmethod
    def in_list(expression: str, *items) -> Predicate:
        """Create list cheking predicate"""

        return InList(expression,  *items)

    @staticmethod
    def equal(expression: str, value: Any) -> Predicate:
        """Create equality cheking predicate"""

        return Equal(expression, value)

    @staticmethod
    def url(pattern: str) -> Predicate:
        """Create url cheking predicate"""

        return Url(pattern)

    @staticmethod
    def between(expression: str, min_value: int, max_value: int) -> Predicate:
        """Create between cheking predicate"""

        return Between(expression, min_value, max_value)

    @staticmethod
    def not_equal(expression: str, value: Any) -> Predicate:
        """Create not equality cheking predicate"""

        return NotEqual(expression, value)

    @staticmethod
    def greater_than(expression: str, value: int) -> Predicate:
        """Create not greater than cheking predicate"""

        return GreaterThan(expression, value)

    @staticmethod
    def less_than(expression: str, value: int) -> Predicate:
        """Create not less than cheking predicate"""

        return LessThan(expression, value)

    @staticmethod
    def less_than_equal(expression: str, value: int) -> Predicate:
        """Create not less than and equal cheking predicate"""

        return LessThanEqual(expression, value)

    @staticmethod
    def greater_than_equal(expression: str, value: int) -> Predicate:
        """Create not less than and equal cheking predicate"""

        return GreaterThanEqual(expression, value)

    @staticmethod
    def match(expression: str, value: str) -> Predicate:
        """Create regex matching cheking predicate"""

        return Match(expression, value)

    @staticmethod
    def has_value(expression: str) -> Predicate:
        """Create has value cheking predicate"""

        return HasValue(expression)
