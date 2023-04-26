from ..cache.manager import CacheManager
from ..cache.cache_status import CacheStatus

class NoCacheManager(CacheManager):
    """"Implementing non caching. Only palace holder for None setting"""

    def cache_decorator(self, key: str, life_time: int = None):
        def decorator(function):
            return function
        return decorator
    
    def get_cache(self, key: str) -> list:
        return list()
    
    def add_or_update(self, key: str, data: "any", life_time: int = None) -> CacheStatus:
        return CacheStatus.NONE
    
    def _update(self, key: str, data: "any", life_time: int = None) -> bool:
        return False
    
    def remove(self, key: str, data: "any") -> CacheStatus:
        return CacheStatus.NONE

    def clean(self) -> None:
        pass

    def reset(self, keys: list[str] = None) -> None:
        pass