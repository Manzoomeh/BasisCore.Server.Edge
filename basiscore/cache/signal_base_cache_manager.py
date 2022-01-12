from basiscore.utility import DictEx
from ..cache.signaler import factory
from ..cache.cache_manager import CacheManager


class SignalBaseCacheManager(CacheManager):
    """Signal base cache manager"""

    def __init__(self, options: DictEx) -> None:
        super().__init__()
        self._options = options
        signaler_option = options.signaler if options is not None and "signaler" in options else None
        self._signaler = factory.create_signaler(
            signaler_option, self.reset_cache)
