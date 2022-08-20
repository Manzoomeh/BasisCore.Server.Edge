import collections
from datetime import timedelta
from datetime import datetime
from functools import wraps
from typing import Callable
from bclib.utility import DictEx
from ..cache.signal_base_cache_manager import SignalBaseCacheManager


class InMemoryCacheManager(SignalBaseCacheManager):
    """Implement in memory cache manager"""

    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        self.__cache_list: 'dict[str, list[Callable]|any]' = dict()

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

    def reset_cache(self, keys: 'list[str]') -> None:
        """Remove key related cache"""

        print(f"reset cache for {keys}")
        for key in keys:
            if key in self.__cache_list:
                if isinstance(self.__cache_list[key], collections.abc.Sequence):
                    for function in self.__cache_list[key]:
                        function.cache = None
                else:
                    self.__cache_list[key] = None

    def get_cache(self, key: str) -> list:
        """Get key related cached data"""

        return ([function.cache for function in self.__cache_list[key]]
                if isinstance(self.__cache_list[key], collections.abc.Sequence)
                else self.__cache_list[key]) if key in self.__cache_list else None

    def update_cache(self, key: str, data: any) -> bool:
        """Update key related cached data"""

        is_successful = False
        if key in self.__cache_list:
            if isinstance(self.__cache_list[key], collections.abc.Sequence):
                for function in self.__cache_list[key]:
                    function.cache = data
            else:
                self.__cache_list[key] = data
            is_successful = True
        return is_successful

    def add_or_update_cache(self, key: str, data: any) -> bool:
        """Add or update key related cached data"""

        is_successfully = self.update_cache(key, data)
        if not is_successfully:
            self.__cache_list[key] = data
        return is_successfully
