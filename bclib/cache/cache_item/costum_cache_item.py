from ..cache_item.base_cache_item import BaseCacheItem

class CostumCacheItem(BaseCacheItem):
    def __init__(self, data: "any", life_time: int) -> None:
        super().__init__(data, life_time)