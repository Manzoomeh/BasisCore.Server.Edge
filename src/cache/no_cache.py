from .cache_manager import CacheManager


class NoCacheManager(CacheManager):
    """"Implementing non caching. Only palace holder for None setting"""

    def cache_decorator(self, seconds: int = 0, key: str = None):
        def decorator(function):
            return function
        return decorator

    def reset_cache(self, key: str):
        pass
