
from datetime import timedelta
from datetime import datetime
from functools import wraps
from typing import Callable
from .signal_base_cache_manager import SignalBaseCacheManager


class InMemoryCacheManager(SignalBaseCacheManager):
    """Implement in memory cache manager"""

    def __init__(self, options: dict) -> None:
        super().__init__(options)
        self.__cache_list: dict[str, list[Callable]] = dict()

    def cache_decorator(self, seconds: int = 0, key: str = None):
        """Cache result of function for seconds of time or until signal by key for clear"""

        def decorator(function):
            function.cache = None
            if seconds > 0:
                function.lifetime = timedelta(seconds=seconds)
                function.expiration = datetime.utcnow() + function.lifetime
            if key is not None:
                if key not in self.__cache_list:
                    self.__cache_list[key] = list()
                self.__cache_list[key].append(function)

            @wraps(function)
            def wrapper_with_time(*args, **kwargs):
                if function.cache is not None and datetime.utcnow() >= function.expiration:
                    function.cache = None
                    function.expiration = datetime.utcnow() + function.lifetime
                if function.cache is None:
                    function.cache = function(*args, **kwargs)
                return function.cache

            @wraps(function)
            def wrapper_without_time(*args, **kwargs):
                if function.cache is None:
                    function.cache = function(*args, **kwargs)
                return function.cache
            return wrapper_with_time if seconds > 0 else wrapper_without_time
        return decorator

    def reset_cache(self, key: str):
        """Remove key related cache"""

        if key in self.__cache_list:
            for function in self.__cache_list[key]:
                function.cache = None
