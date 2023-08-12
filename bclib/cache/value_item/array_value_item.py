from bclib.cache.cache_item.base_cache_item import BaseCacheItem
from ..value_item.base_value_item import BaseValueItem
from ..cache_item.function_cache_item import FunctionCacheItem

class ArrayValueItem(BaseValueItem):

    def _apply_item(self, cache_item: "BaseCacheItem") -> "list[BaseCacheItem]":
        if self._item is None:
            self._item = list()
        self._item.append(cache_item)
