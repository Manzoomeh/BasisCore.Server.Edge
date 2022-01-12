from ..cache.cache_manager import CacheManager


class NoCacheManager(CacheManager):
    """"Implementing non caching. Only palace holder for None setting"""

    def cache_decorator(self, seconds: int = 0, key: str = None):
        def decorator(function):
            return function
        return decorator

    def reset_cache(self, keys: list[str]):
        pass

    def get_cache(self, key: str) -> list:
        pass

    def update_cache(self, key: str, data: any) -> bool:
        pass
