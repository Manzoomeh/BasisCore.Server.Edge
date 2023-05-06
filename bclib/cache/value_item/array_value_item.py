from bclib.cache.cache_item.base_cache_item import BaseCacheItem
from ..value_item.base_value_item import BaseValueItem

class ArrayValueItem(BaseValueItem):
            
    def _apply_item(self, cache_item: "BaseCacheItem") -> "list[BaseCacheItem]":
        return [cache_item]
    
    def add_or_update_item(self, cache_item: "BaseCacheItem"):
        self._item.append(cache_item)

    def reset(self):
        self._item = list()