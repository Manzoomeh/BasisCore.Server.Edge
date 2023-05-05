from bclib.cache.cache_item.base_cache_item import BaseCacheItem
from ..value_item.base_value_item import BaseValueItem

class ScalarValueItem(BaseValueItem):
    def _apply_item(self, cache_item: "BaseCacheItem") -> "BaseCacheItem":
        return cache_item
    
    def add_or_update_item(self, cache_item: "BaseCacheItem"):
        if self._item is not None:
            raise TypeError("ScalarValueItem does not support this type of action!")
        else:
            self._item = self._apply_item(cache_item)
