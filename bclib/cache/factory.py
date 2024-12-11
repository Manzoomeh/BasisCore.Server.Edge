from cache.cache_manager import CacheManager
from abc import ABC
from bclib.utility import DictEx
from bclib.cache.in_memory_cache_manager import InMemoryCacheManager
from bclib.cache.no_cache import NoCacheManager


class CacheFactory(ABC):
    @staticmethod
    def create(options: "DictEx" = None) -> "CacheManager":
        cache_type = str(options.type) if options is not None and options.has(
            "type") else None
        if cache_type is not None:
            if cache_type == "memory":
                return InMemoryCacheManager(options)
            else:
                raise ValueError(f"Unknown type for cache ('${cache_type}')")
        return NoCacheManager(options)
