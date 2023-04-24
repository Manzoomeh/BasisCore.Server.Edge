
"""Represent no chanching"""
from abc import ABC, abstractmethod
from bclib.utility import DictEx
from ..cache.cache_item.base_cache_item import BaseCacheItem
class CacheManager(ABC):
    """Represent no chanching"""

    @abstractmethod
    def cache_decorator(self, key:"str", seconds:"int"=0):
        """Cache result of function for seconds of time or until signal by key for clear"""

    @abstractmethod
    def reset_cache(self, keys: "list[str]"):
        """Remove key related cache"""

    @abstractmethod
    def get_cache(self, key: str) -> "list[BaseCacheItem]":
        """Get key related cached data"""

    @abstractmethod
    def _update_cache_list(self, key: str, data: any) -> "bool":
        """Update key related cached data"""

    @abstractmethod
    def add_or_update_cache_list(self, key: str, data: any) -> "DictEx":
        """Add or update key related cached data"""
