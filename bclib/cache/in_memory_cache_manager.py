import collections
from datetime import timedelta
from datetime import datetime
from functools import wraps
from typing import Callable
from bclib.utility import DictEx
from ..cache.signal_base_cache_manager import SignalBaseCacheManager
from ..cache.cache_item.base_cache_item import BaseCacheItem
from ..cache.cache_item.function_cache_item import FunctionCacheItem
from ..cache.cache_item.costum_cache_item import CostumCacheItem
from ..cache.cache_item.cache_status import CacheStatus
class InMemoryCacheManager(SignalBaseCacheManager):
    """Implement in memory cache manager"""

    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        self.__cache_list: 'dict[str, list[BaseCacheItem]]' = dict()

    def cache_decorator(self, key:"str", seconds:"int"=0):
        """Cache result of function for seconds of time or until signal by key for clear"""

        def decorator(function):
            function.cache = None
            if key is not None:
                cache_item = FunctionCacheItem(None, seconds, function)
                if key not in self.__cache_list:
                    self.__cache_list[key] = list()
                self.__cache_list[key].append(cache_item)
                function.cache = cache_item
            else:
                raise Exception("key is None!")

            @wraps(function)
            def wrapper(*args, **kwargs):
                data:"any" = None
                function_cache:"FunctionCacheItem|None" = function.cache
                if function_cache is not None:
                    data = function_cache.data if not function_cache.is_expired else None
                    if data is None:
                        data = function(*args, **kwargs)
                        function_cache.update_data(data)
                else:
                    data = function(*args, **kwargs)
                    function.cache = FunctionCacheItem(data, seconds, function)
                return data
            return wrapper
        return decorator

    def reset_cache(self, keys: 'list[str]') -> None:
        """reset data related to key in cache list"""
        for key in keys:
            if key in self.__cache_list:
                for item in self.__cache_list[key]:
                    item.update_data(None)

    def get_cache(self, key:"str") -> "list[BaseCacheItem]":
        """Get key related cached data"""
        ret_val = list()
        if key in self.__cache_list:
            for item in self.__cache_list[key]:
                ret_val.append(item)
        return ret_val

    def _update_cache_list(self, key:"str", cache_item:"BaseCacheItem") -> bool:
        """Update key related cached data"""
        is_successful = False
        if key in self.__cache_list:
            key_cache = self.__cache_list[key]
            key_cache.append(cache_item)
            is_successful = True
        return is_successful

    def add_or_update_cache_list(self, key:"str", data:"any", seconds:"int"=0) -> "DictEx":
        """Add or update key related cached data"""
        cache_item = CostumCacheItem(data, seconds)
        is_successfully = self._update_cache_list(key, cache_item)
        if not is_successfully:
            self.__cache_list[key] = [cache_item]
        return DictEx({
            "status": CacheStatus.ADDED if not is_successfully else CacheStatus.UPDATED
        })
