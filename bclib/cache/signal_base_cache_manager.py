from ..cache.manager import CacheManager
from bclib.utility import DictEx
from abc import abstractmethod
from ..cache.signaler.factory import SignalerFactory

class SignalBaseCacheManager(CacheManager):
    DEFAULT_MAX_SIZE = 10000 # -1 for unlimited
    DEFAULT_LIFE_TIME = 900 #Seconds => 15 Minutes
    DEFAULT_MAX_LIFE_TIME = 21600 #Seconds => 6 Hours ; -1 for indefinitely
    DEFAULT_CLEAN_INTERVAL = 43200 #Seconds => 12 Hours ; -1 for keep all cache data for ever

    def __init__(self, options: "DictEx") -> None:
        super().__init__(options)
        self.__max_size = int(self._options.max_size) if self._options.has("max_size") else SignalBaseCacheManager.DEFAULT_MAX_SIZE
        self._default_life_time = SignalBaseCacheManager.DEFAULT_LIFE_TIME
        self._max_life_time = int(self._options.max_life_time) if self._options.has("max_life_time") else SignalBaseCacheManager.DEFAULT_MAX_LIFE_TIME
        self.__interval = int(self._options.clean_interval) if self._options.has("clean_interval") else SignalBaseCacheManager.DEFAULT_CLEAN_INTERVAL
        signaler_options = self._options.signaler if self._options.has("signaler") else None
        self._reset_signaler = SignalerFactory.create(self.reset, signaler_options)
        # self._check_size = self.__max_size != -1
        # self._clear_cache = self.__interval != -1

    @abstractmethod
    def _size(self): ...


    @property
    def _is_valid_size(self):
        return self._size() <= self.__max_size if self.__max_size != 1 else True
    
    @abstractmethod
    def _clean(self): ...

    def clean(self) -> None:
        if self.__interval != -1:
            self._clean()