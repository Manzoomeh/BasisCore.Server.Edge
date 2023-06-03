from bclib.cache.cache_item.base_cache_item import BaseCacheItem
from ..value_item.base_value_item import BaseValueItem

class ScalarValueItem(BaseValueItem):
    def _apply_item(self, cache_item: "BaseCacheItem") -> "BaseCacheItem":
        return cache_item
    
    def add_or_update_item(self, cache_item: "BaseCacheItem"):
        raise TypeError("ScalarValueItem does not support this type of action!")

    def reset(self):
        self._item = None