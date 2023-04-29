from abc import ABC, abstractmethod
from bclib.utility import DictEx
from ..cache.cache_status import CacheStatus

class CacheManager(ABC):
    def __init__(self, options:"DictEx") -> None:
        super().__init__()
        self._options = options

    @abstractmethod
    def cache_decorator(self, key:"str", life_time:"int"=None): ...

    @abstractmethod
    def get_cache(self, key:"str") -> "list|None": ...

    @abstractmethod
    def _update(self, key:"str", data:"any", life_time:"int"=None) -> "bool": ...
    
    @abstractmethod
    def add_or_update(self, key:"str", data:"any", life_time:"int"=None) -> "CacheStatus": ...

    @abstractmethod
    def set_data(self, key:"str", data:"any", life_time:"int"=None) -> "CacheStatus": ...

    @abstractmethod
    def remove(self, key:"str", data:"any") -> "CacheStatus": ...
    
    @abstractmethod
    def clean(self) -> "CacheStatus": ...

    @abstractmethod
    def reset(self, keys:"list[str]"=None) -> "CacheStatus": ...
