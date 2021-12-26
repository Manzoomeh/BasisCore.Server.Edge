
"""Represent no chanching"""
from abc import ABC, abstractmethod


class CacheManager(ABC):
    """Represent no chanching"""

    @abstractmethod
    def cache_decorator(self, seconds: int = 0, key: str = None):
        """Cache result of function for seconds of time or until signal by key for clear"""

    @abstractmethod
    def reset_cache(self, key: list[str]):
        """Remove key related cache"""

    @abstractmethod
    def get_cache(self, key: str) -> list:
        """Get key related cached data"""

    @abstractmethod
    def update_cache(self, key: str, data: any) -> bool:
        """Update key related cached data"""
