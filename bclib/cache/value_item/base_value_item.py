from abc import ABC, abstractmethod
from ..cache_item.base_cache_item import BaseCacheItem
from ..cache_item.function_cache_item import FunctionCacheItem

class BaseValueItem(ABC):
    def __init__(self, cache_item:"BaseCacheItem") -> None:
        super().__init__()
        self._item:"list[BaseCacheItem]|BaseCacheItem" = None
        self._apply_item(cache_item)
    
    @abstractmethod
    def _apply_item(self, cache_item:"BaseCacheItem"): ...

    def add_or_update_item(self, cache_item: "BaseCacheItem"):
        self._apply_item(cache_item)
    
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
        # Function cache items stay registered (the decorated function keeps
        # using them), so only their entries are cleared; other items are dropped.
        items = self._item if isinstance(self._item, list) else [self._item]
        kept = [item for item in items if isinstance(item, FunctionCacheItem)]
        for item in kept:
            item.reset()
        if not kept:
            self._item = None
        elif isinstance(self._item, list):
            self._item = kept
        else:
            self._item = kept[0]

    def is_registered_function(self) -> bool:
        """True if this value holds a decorated function's cache (never cleaned away)"""
        items = self._item if isinstance(self._item, list) else [self._item]
        return any(isinstance(item, FunctionCacheItem) for item in items)

