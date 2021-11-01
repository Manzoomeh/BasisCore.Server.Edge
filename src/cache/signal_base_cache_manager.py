from .cache_manager import CacheManager


class SignalBaseCacheManager(CacheManager):
    """Signal base cache manager"""

    def __init__(self, options: dict) -> None:
        super().__init__()
        self._options = options
