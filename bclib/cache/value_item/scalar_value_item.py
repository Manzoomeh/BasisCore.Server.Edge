from bclib.cache.cache_item.base_cache_item import BaseCacheItem
from bclib.cache.value_item.base_value_item import BaseValueItem


class ScalarValueItem(BaseValueItem):

    def _apply_item(self, cache_item: "BaseCacheItem") -> "BaseCacheItem":
        self._item = cache_item
