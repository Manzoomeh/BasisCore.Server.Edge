from ..cache_item.base_cache_item import BaseCacheItem
from typing import Callable

class FunctionCacheItem(BaseCacheItem):
    def __init__(self, data: "any", life_time: "int" = 0, function:"Callable"=None) -> None:
        super().__init__(data, life_time)
        self.__function = function
        