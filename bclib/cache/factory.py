from ..cache.manager import CacheManager
from abc import ABC
from bclib.utility import DictEx
from ..cache.memory_cache_factory import InMemoryCacheFactory
from ..cache.no_cache import NoCacheManager

class CacheFactory(ABC):
    @staticmethod
    def create(options:"DictEx"=None) -> "CacheManager":
        cache_type = str(options.type) if options is not None and options.has("type") else None
        if cache_type is not None:
            if cache_type == "memory":
                return InMemoryCacheFactory.create(options)
        return NoCacheManager(options)