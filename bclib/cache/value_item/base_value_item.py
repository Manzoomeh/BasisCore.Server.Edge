from abc import ABC, abstractmethod
from ..cache_item.base_cache_item import BaseCacheItem

class BaseValueItem(ABC):
    def __init__(self, cache_item:"BaseCacheItem") -> None:
        super().__init__()
        self._item:"list[BaseCacheItem]|BaseCacheItem" = self._apply_item(cache_item)
    
    @abstractmethod
    def _apply_item(self, cache_item:"BaseCacheItem"): ...

    @abstractmethod
    def add_or_update_item(self, cache_item: "BaseCacheItem"): ...
    
    def get_item(self) -> "list|any|None":
        if self._item is not None:
            if isinstance(self._item, list):
                ret_val = list()
                for item in self._item:
                    data = item.data()
                    if data is not None:
                        ret_val.append(data)
                return ret_val if len(ret_val) > 0 else None
            else:
                ret_val = self._item.data()
        else:
            ret_val = None
        return ret_val
    
    def reset(self):
        self._item = None

