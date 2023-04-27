from ..cache.in_memory_cache_manager import InMemoryCacheManager
from bclib.utility import DictEx
from ..cache.cache_status import CacheStatus
from typing import Callable
from ..cache.cache_item.base_cache_item import BaseCacheItem
from ..cache.cache_item.function_cache_item import FunctionCacheItem
from ..cache.cache_item.costum_cache_item import CostumCacheItem
from functools import  wraps
from collections import OrderedDict

class DictMemoryCacheManager(InMemoryCacheManager):
    
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        self.__cache_dict:"OrderedDict[str, list[BaseCacheItem]]" = OrderedDict()

    def _size(self):
        return len(self.__cache_dict)

    def _add_to_cache(self, key:"str", cache_item:"BaseCacheItem") -> None:
        """
        Adds a cache item to the cache dictionary with the specified key.

        Args:
            key (str): The key for the cache item.
            cache_item (BaseCacheItem): The cache item to add to the dictionary.

        Returns:
            None

        Raises:
            None
        """
        if key in self.__cache_dict:
            self.__cache_dict[key].append(cache_item)
            self.__cache_dict.move_to_end(key)
        else:
            self.__cache_dict[key] = [cache_item]
            if not self._is_valid_size:
                self.__cache_dict.popitem(last=False)

    def cache_decorator(self, key:"str", life_time:"int"="None") -> "Callable":
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
        life_time = min(life_time, self._max_life_time) if life_time is not None else self._default_life_time
        def decorator(function):
            if key is not None:
                cache_item = FunctionCacheItem(None, life_time, function)
                function.cache = cache_item
                self._add_to_cache(key, cache_item)
            else:
                raise ValueError("key is None!")

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
            self.__cache_dict = OrderedDict()
        else:
            for key in keys:
                if key in self.__cache_dict:
                    self.__cache_dict.pop(key)
        return CacheStatus.RESET

    def _clean(self) -> "CacheStatus":
        """
        Removes expired cache items from the cache dictionary.
        """
        valid_cache_dict = OrderedDict()
        for key in self.__cache_dict:
            valid_cache_list = list()
            for item in self.__cache_dict[key]:
                if item.data() is not None:
                    valid_cache_list.append(item)
            if len(valid_cache_list) > 0:
                valid_cache_dict[key] = valid_cache_list
        self.__cache_dict = valid_cache_dict
        return CacheStatus.CLEANED

    def get_cache(self, key:"str") -> "list":
        """
        Returns the data associated with the cache items for a given key.

        Args:
            key (str): The key to look up in the cache dictionary.

        Returns:
            list: The data associated with the cache items for the given key.

        Raises:
            None
        """
        if key in self.__cache_dict:
            self.__cache_dict.move_to_end(key)
            print("ITEMS: ", self.__cache_dict[key])
            return [
                item.data() for item in self.__cache_dict[key]
                if item.data() is not None
            ]
        return []
    
    def _update(self, key:"str", data:"any", life_time:"int"=None) -> "bool":
        """
        Updates the cache item for a given key with the specified data and lifetime.
        """
        updated = False
        if key in self.__cache_dict:
            self.__cache_dict[key].append(CostumCacheItem(data, life_time))
            self.__cache_dict.move_to_end(key)
            updated = True
        return updated
    
    def add_or_update(self, key:"str", data:"any", life_time:"int"=None) -> "CacheStatus":
        """
        Add or update an item in the cache.

        Args:
            key (str): The key to identify the cache item.
            data (any): The data to be stored in the cache.
            life_time (int, optional): The time-to-live (TTL) of the cache item in seconds. If None, the default life time of the cache will be used.

        Returns:
            CacheStatus: The status of the cache after adding or updating the item. Returns CacheStatus.ADDED if a new item was added to the cache, and CacheStatus.UPDATED if an existing item was updated.        
        """
        is_updated = self._update(key, data, life_time)
        if not is_updated:
            self._add_to_cache(key, CostumCacheItem(data, life_time))
            return CacheStatus.ADDED
        return CacheStatus.UPDATED

    def remove(self, key:"str", data:"any") -> "CacheStatus":
        """
        Removes a specific cache item with a given key and data from the cache.

        Args:
        - key (str): The cache key to remove the data from.
        - data (any): The data to be removed from the cache.

        Returns:
        - CacheStatus.REMOVED if the item was successfully removed from the cache.
        - CacheStatus.NONE if the item was not found in the cache.
        """
        if key in self.__cache_dict:
            selected_item = None
            cache_list = self.__cache_dict[key]
            for item in cache_list:
                if item.data() == data:
                    selected_item = item
                    break
            if selected_item is not None:
                cache_list.remove(selected_item)
                return CacheStatus.REMOVED
        return CacheStatus.NONE

    def set_data(self, key:"str", data:"any", life_time:"int"=None) -> "CacheStatus":
        """
        Sets the cache for a given key with the provided data and life_time.
        If the key already exists, its previous value will be overwritten with the new data.

        Args:
            key (str): The key to be set in the cache.
            data (Any): The data to be cached.
            life_time (int, optional): The maximum time in seconds that the data should be kept in the cache.
                                    If None, the default lifetime of the cache will be used.

        Returns:
            CacheStatus: The status of the cache after the set operation.
                        Returns CacheStatus.SET if a new cache item was added, or CacheStatus.UPDATED
                        if an existing cache item was updated with new data.
        """
        self.__cache_dict[key] = [CostumCacheItem(data, life_time)]
        self.__cache_dict.move_to_end(key)
        return CacheStatus.SET