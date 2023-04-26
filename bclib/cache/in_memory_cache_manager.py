from ..cache.signal_base_cache_manager import SignalBaseCacheManager
from bclib.utility import DictEx
from abc import abstractmethod
from ..cache.cache_item.base_cache_item import BaseCacheItem

class InMemoryCacheManager(SignalBaseCacheManager):
    def __init__(self, options:"DictEx") -> None:
        super().__init__(options)

    @abstractmethod
    def _add_to_cache(self, key:"str", cache_item:"BaseCacheItem") -> "None": ...