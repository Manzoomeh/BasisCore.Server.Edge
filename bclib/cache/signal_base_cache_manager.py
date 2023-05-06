from ..cache.manager import CacheManager
from bclib.utility import DictEx
from ..cache.signaler.factory import SignalerFactory
import asyncio

class SignalBaseCacheManager(CacheManager):
    DEFAULT_CLEAN_INTERVAL = 43200 #Seconds => 12 Hours; 0 for indefinitely
    DEFAULT_RESET_INTERVAL = 86400 #Seconds => 24 Hours; 0 for indefinitely

    def __init__(self, options: "DictEx") -> None:
        super().__init__(options)
        self.__clean_interval = int(self._options.clean_interval) if self._options.has("clean_interval") else SignalBaseCacheManager.DEFAULT_CLEAN_INTERVAL
        if self.__clean_interval < 0:
            raise ValueError("Invalid input for clean_interval!")
        self.__reset_interval = int(self._options.reset_interval) if self._options.has("reset_interval") else SignalBaseCacheManager.DEFAULT_RESET_INTERVAL
        if self.__reset_interval < 0:
            raise ValueError("Invalid input for reset_interval!")
        signaler_options = self._options.signaler if self._options.has("signaler") else None
        self._reset_signaler = SignalerFactory.create(self.reset, signaler_options)
        if self.__reset_interval > 0 or self.__clean_interval > 0:
            loop = asyncio.get_event_loop()
            if self.__reset_interval > 0:
                loop.create_task(self.__reset_async(self.__reset_interval))
            if self.__reset_interval > 0:
                loop.create_task(self.__clean_async(self.__reset_interval))
    
    async def __reset_async(self, interval:"int"):
        try:
            while True:
                await asyncio.sleep(interval)
                self.reset()
        except: ...

    async def __clean_async(self, interval:"int"):
        try:
            while True:
                await asyncio.sleep(interval)
                self.clean()
        except: ...
