from .cache_manager import CacheManager
from .in_memory_cache_manager import InMemoryCacheManager
from .no_cache import NoCacheManager


def create_chaching(options: dict) -> CacheManager:
    ret_val: CacheManager = None
    cache_type = options["type"] if options is not None else "none"
    if cache_type == "memory":
        ret_val = InMemoryCacheManager(options)
    elif cache_type == "none":
        ret_val = NoCacheManager()
    return ret_val
