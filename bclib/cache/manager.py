from abc import ABC, abstractmethod
from bclib.utility import DictEx
from ..cache.cache_status import CacheStatus

class CacheManager(ABC):
    def __init__(self, options:"DictEx") -> None:
        super().__init__()
        self._options = options

    @abstractmethod
    def cache_decorator(self, key:"str"=None, life_time:"int"=0): ...

    @abstractmethod
    def get_cache(self, key:"str") -> "list|any|None": ...
    
    @abstractmethod
    def add_or_update(self, key:"str", data:"any", life_time:"int"=0) -> "CacheStatus": ...
    
    @abstractmethod
    def clean(self) -> "CacheStatus": ...

    @abstractmethod
    def reset(self, keys:"list[str]"=None) -> "CacheStatus": ...
