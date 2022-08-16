from bclib.utility import DictEx
from ..cache.cache_manager import CacheManager
from ..cache.in_memory_cache_manager import InMemoryCacheManager
from ..cache.initial_memory_cache_manager import InitialMemoryCacheManager
from ..cache.no_cache import NoCacheManager


def create_caching(options: DictEx) -> CacheManager:
    ret_val: CacheManager = None
    cache_type = options.type if options is not None and "type" in options else "none"
    if cache_type == "memory":
        ret_val = InMemoryCacheManager(options)
    elif cache_type == "initial_memory":
        ret_val = InitialMemoryCacheManager(options)
    elif cache_type == "none":
        ret_val = NoCacheManager()
    else:
        raise Exception(
            f"unknown type for cache ('${cache_type}')")
    return ret_val
