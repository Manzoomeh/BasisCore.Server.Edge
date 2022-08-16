from datetime import timedelta
from datetime import datetime
from functools import wraps
from typing import Callable
from bclib.utility import DictEx
from ..cache.signal_base_cache_manager import SignalBaseCacheManager


class InitialMemoryCacheManager(SignalBaseCacheManager):
    """Implement initial memory cache manager"""

    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        self.__cache_data: 'dict[str, dict[str, any]]' = dict()

    def cache_decorator(self, seconds: int = 0, key: str = None):
        """Cache data when service run"""

        def decorator(function):
            print("function", function)
            keys = key.split(",")
            data = function()
            self.__cache_data.update(dict(zip(keys, data)))

            return data

        return decorator

    def reset_cache(self, keys: 'list[str]') -> None:
        """Remove key related cache"""

        print(f"reset cache for {keys}")
        for key in keys:
            self.__cache_data.pop(key, None)

    def get_cache(self, key: str) -> dict:
        """Get key related cached data"""

        return self.__cache_data[key] if key in self.__cache_data else None

    def update_cache(self, key: str, data: any) -> bool:
        """Update key related cached data"""

        is_siccessfull = False
        if key in self.__cache_data:
            self.__cache_data[key] = data
            is_siccessfull = True
        return is_siccessfull

    def hget_cache(self, key: str, sub_key: str) -> any:
        return self.__cache_data.get(key, {}).get(sub_key, None)

    def hupdate_cache(self, key: str, sub_key: str, data: any) -> bool:
        is_siccessfull = False
        if key in self.__cache_data:
            if sub_key in self.__cache_data[key]:
                self.__cache_data[key][sub_key] = data
                is_siccessfull = True
        return is_siccessfull
