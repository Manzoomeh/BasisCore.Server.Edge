from ..cache.in_memory_cache_manager import InMemoryCacheManager
from bclib.utility import DictEx
from ..cache.cache_status import CacheStatus
from typing import Callable
from ..cache.cache_item.base_cache_item import BaseCacheItem
from ..cache.cache_item.function_cache_item import FunctionCacheItem
from ..cache.cache_item.costum_cache_item import CostumCacheItem
from functools import  wraps

class DictMemoryCacheManager(InMemoryCacheManager):
    
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        self.__cache_dict:"dict[str, list[BaseCacheItem]]" = dict()

    @property
    def _size(self):
        return len(self.__cache_dict)

    def _add_to_cache(self, key:"str", cache_item:"BaseCacheItem") -> None:
        key_cache = self.__cache_dict[key] if key in self.__cache_dict else []
        key_cache.append(cache_item)
        if key not in self.__cache_dict:
            self.__cache_dict[key] = key_cache
            if not self._is_valid_size:
                first_key = list(self.__cache_dict.keys())[0]
                self.__cache_dict.pop(first_key)
        else:
            self.__cache_dict[key] = key_cache

    def cache_decorator(self, key:"str", life_time:"int"="None") -> "Callable":
        life_time = min(life_time, self._max_life_time) if life_time is not None else self._default_life_time
        def decorator(function):
            if key is not None:
                function.cache = FunctionCacheItem(None, life_time, function)
            else:
                raise ValueError("key is None!")

            @wraps(function)
            def wrapper(*args, **kwargs):
                function_cache:"FunctionCacheItem" = function.cache
                return function_cache.get_data(args, kwargs)
            return wrapper
        return decorator

    def reset(self, keys: list[str] = None) -> None:
        if keys is None or len(keys) == 0:
            self.__cache_dict = dict()
        else:
            for key in keys:
                if key in self.__cache_dict:
                    self.__cache_dict.pop(key)

    def _clean(self):
        valid_cache_dict = dict()
        for key in self.__cache_dict:
            valid_cache_list = list()
            for item in self.__cache_dict[key]:
                if item.data() is not None:
                    valid_cache_list.append(item)
            if len(valid_cache_list) > 0:
                valid_cache_dict[key] = valid_cache_list
        self.__cache_dict = valid_cache_dict

    def get_cache(self, key:"str") -> "list":
        return [
            item.data() for item in self.__cache_dict[key]
        ] if key in self.__cache_dict else []
    
    def _update(self, key:"str", data:"any", life_time:"int"=None) -> "bool":
        updated = False
        if key in self.__cache_dict:
            self.__cache_dict[key].append(CostumCacheItem(data, life_time))
        return updated
    
    def add_or_update(self, key:"str", data:"any", life_time:"int"=None) -> "CacheStatus":
        is_updated = self._update(key, data, life_time)
        if not is_updated:
            self._add_to_cache(key, CostumCacheItem(data, life_time))
            return CacheStatus.ADDED
        return CacheStatus.UPDATE

    def remove(self, key:"str", data:"any") -> "CacheStatus":
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
