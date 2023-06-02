from bclib.cache.cache_status import CacheStatus
from ..cache.signal_base_cache_manager import SignalBaseCacheManager
from bclib.utility import DictEx
from ..cache.cache_status import CacheStatus
from typing import Callable
from ..cache.cache_item.base_cache_item import BaseCacheItem
from ..cache.cache_item.function_cache_item import FunctionCacheItem
from .cache_item.scalar_cache_item import ScalarCacheItem
from ..cache.value_item.base_value_item import BaseValueItem
from ..cache.value_item.array_value_item import ArrayValueItem
from ..cache.value_item.scalar_value_item import ScalarValueItem
from functools import wraps

class InMemoryCacheManager(SignalBaseCacheManager):
    
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        self.__cache_dict:"dict[str, BaseValueItem]" = dict()

    def __add_or_update(self, key:"str", cache_item:"BaseCacheItem", value_item:"BaseValueItem") -> "CacheStatus":
        if key not in self.__cache_dict:
            self.__cache_dict[key] = value_item(cache_item)
            return CacheStatus.ADDED
        else:
            try:
                self.__cache_dict[key].add_or_update_item(cache_item)
                return CacheStatus.UPDATED
            except TypeError as ex:
                print(repr(ex))
                return CacheStatus.ERROR

    def cache_decorator(self, key:"str"=None, life_time:"int"=0) -> "Callable":
        """
        Decorator that caches the result of a function for a specified key and life time.

        Args:
            key (str): The key to use for caching the function's result.
            life_time (int): The life time of the cache item in seconds. If not specified, uses the default life time.

        Returns:
            Callable: The decorated function.

        Raises:
            ValueError: If the key is None.
        """
        def decorator(function):
            cache_item = FunctionCacheItem(None, life_time, function)
            function.cache = cache_item
            if key is not None:
                self.__add_or_update(key, cache_item, ArrayValueItem)

            @wraps(function)
            def wrapper(*args, **kwargs):
                function_cache:"FunctionCacheItem" = function.cache
                return function_cache.get_data(*args, **kwargs)
            return wrapper
        return decorator

    def reset(self, keys:"list[str]"=None) -> "CacheStatus":
        """
        Resets the cache by removing all items or specified keys.

        Args:
            keys (list[str]): Optional list of keys to remove from the cache. If not specified, removes all items.

        Returns:
            CacheStatus: The status of the cache after the reset operation.

        Raises:
            None
        """
        if keys is None or len(keys) == 0:
            keys = list(self.__cache_dict.keys())
        for key in keys:
            self.__cache_dict[key].reset()
        return CacheStatus.RESET

    def clean(self) -> "CacheStatus":
        """
        Removes expired cache items from the cache dictionary.
        """
        cleaned_cache_dict = dict()
        for key, value in self.__cache_dict.items():
            if value.get_item() is not None:
                cleaned_cache_dict[key] = value
        self.__cache_dict = cleaned_cache_dict
        return CacheStatus.CLEANED

    def get_cache(self, key:"str") -> "list|any|None":
        return self.__cache_dict[key].get_item() if key in self.__cache_dict else None
    
    def add_or_update(self, key: str, data: "any", life_time:"int"= 0) -> "CacheStatus":
        """
        Add or update an item in the cache.
        Args:
            key (str): The key to identify the cache item.
            data (any): The data to be stored in the cache.
            life_time (int, optional): The time-to-live (TTL) of the cache item in seconds. If 0, the default life time of the cache will be used.

        Returns:
            CacheStatus: The status of the cache after adding or updating the item. Returns CacheStatus.ADDED if a new item was added to the cache, and CacheStatus.UPDATED if an existing item was updated.        
        """
        return self.__add_or_update(key, ScalarCacheItem(data, int(life_time)), ScalarValueItem)
