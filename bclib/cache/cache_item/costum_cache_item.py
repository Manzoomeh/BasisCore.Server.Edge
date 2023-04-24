from ..cache_item.base_cache_item import BaseCacheItem

class CostumCacheItem(BaseCacheItem):
    def __init__(self, data: "any", life_time: "int" = 0) -> None:
        super().__init__(data, life_time)

    def get_data(self, *args, **kwargs) -> "any|None":
        super().get_data()
        return self._data
