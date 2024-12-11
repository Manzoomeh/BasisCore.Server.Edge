from cache.cache_manager import CacheManager
from bclib.cache.cache_status import CacheStatus


class NoCacheManager(CacheManager):
    """"Implementing non caching. Only palace holder for None setting"""

    def cache_decorator(self, key: str = None, life_time: int = 0):
        def decorator(function):
            return function
        return decorator

    def get_cache(self, key: str) -> "list|None":
        return None

    def add_or_update(self, key: str, data: "any", life_time: int = 0) -> CacheStatus:
        return CacheStatus.ERROR

    def clean(self) -> None:
        pass

    def reset(self, keys: 'list[str]' = None) -> None:
        pass
