from ..signaler.base_signaler import BaseSignaler
from bclib.utility import DictEx
from typing import Callable
import asyncio

class TimeSignaler(BaseSignaler):
    DEFAULT_INTERVAL = 86400 #Seconds => 12 Hours ; -1 for keep cache data for ever
    def __init__(self, reset_cache_callback:"Callable", options:"DictEx"="None") -> "None":
        super().__init__(reset_cache_callback, options)
        self.__reset_interval = int(self._options.interval) if self._options.has("interval") else TimeSignaler.DEFAULT_INTERVAL
        if self.__reset_interval != -1:
            asyncio.get_event_loop().create_task(self.__reset_signal())

    async def __reset_signal(self):
        try:
            while True:
                await asyncio.sleep(self.__reset_interval)
                self._callback()
        except asyncio.CancelledError: 
            pass
    