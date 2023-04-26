from ..cache.in_memory_cache_manager import InMemoryCacheManager
from bclib.utility import DictEx
from abc import ABC
from ..cache.dict_cache_manager import DictMemoryCacheManager

class InMemoryCacheFactory(ABC):
    @staticmethod
    def create(options:"DictEx") -> "InMemoryCacheManager":
        if options.has("memory_type") and options.memory_type == "sqlite":
            return None
        return DictMemoryCacheManager(options)
