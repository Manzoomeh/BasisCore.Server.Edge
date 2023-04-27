from ..cache_item.base_cache_item import BaseCacheItem
from typing import Callable

class FunctionCacheItem(BaseCacheItem):
    def __init__(self, data: "any", life_time:"int", function:"Callable") -> None:
        super().__init__(data, life_time)
        self.__function = function

    def get_data(self, *args, **kwargs) -> "any":
        data = self.data()
        if data is None:
            data = self.__function(*args, **kwargs)
            self._update_data(data)
        return data