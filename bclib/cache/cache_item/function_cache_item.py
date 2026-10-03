from ..cache_item.base_cache_item import BaseCacheItem
from ..cache_item.scalar_cache_item import ScalarCacheItem
from typing import Callable, Hashable

class FunctionCacheItem(BaseCacheItem):
    """Caches the results of a function, one entry per distinct set of arguments"""

    def __init__(self, data: "any", life_time:"int", function:"Callable") -> None:
        super().__init__(data, life_time)
        self.__function = function
        self.__life_time = life_time
        self.__entries: "dict[Hashable, ScalarCacheItem]" = dict()
        self.__last_key: "Hashable" = None

    @staticmethod
    def make_key(args: tuple, kwargs: dict) -> "Hashable":
        """Build a cache key from call arguments; falls back to repr() for unhashable values"""
        key = (args, tuple(sorted(kwargs.items())))
        try:
            hash(key)
            return key
        except TypeError:
            return ("repr", repr(key))

    def lookup(self, key: "Hashable") -> "any":
        entry = self.__entries.get(key)
        if entry is None:
            return None
        data = entry.data()
        if data is None:
            del self.__entries[key]
        return data

    def store(self, key: "Hashable", data: "any") -> None:
        if data is not None:
            self.__entries[key] = ScalarCacheItem(data, self.__life_time)
            self.__last_key = key

    def get_data(self, *args, **kwargs) -> "any":
        key = FunctionCacheItem.make_key(args, kwargs)
        data = self.lookup(key)
        if data is None:
            data = self.__function(*args, **kwargs)
            self.store(key, data)
        return data

    async def get_data_async(self, *args, **kwargs) -> "any":
        key = FunctionCacheItem.make_key(args, kwargs)
        data = self.lookup(key)
        if data is None:
            data = await self.__function(*args, **kwargs)
            self.store(key, data)
        return data

    def reset(self) -> None:
        """Drop all cached entries; the next call recomputes"""
        self.__entries.clear()
        self.__last_key = None

    def data(self) -> "any":
        """Drop expired entries and return the most recently stored live value"""
        for key in [k for k, entry in self.__entries.items() if entry.data() is None]:
            del self.__entries[key]
        return self.lookup(self.__last_key)
