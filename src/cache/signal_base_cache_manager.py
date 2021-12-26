from utility import DictEx
from .signaler import factory
from .cache_manager import CacheManager


class SignalBaseCacheManager(CacheManager):
    """Signal base cache manager"""

    def __init__(self, options: DictEx) -> None:
        super().__init__()
        self._options = options
        signaler_option = options.signaler if options is not None and "signaler" in options else None
        self.__signaler = factory.create_signaler(
            signaler_option, lambda keys: self.reset_cache(keys))
