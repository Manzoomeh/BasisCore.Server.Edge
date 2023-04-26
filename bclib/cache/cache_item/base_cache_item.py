from abc import ABC
import time

class BaseCacheItem(ABC):
    MAX_LIFE_TIME = 86400 #Seconds => 1 Day
    def __init__(self, data:"any", life_time:"int") -> None:
        super().__init__()
        self.__data = data
        self.__life_time = min(life_time, BaseCacheItem.MAX_LIFE_TIME) if life_time != -1 else None
        self.__created_time = time.time()

    def __is_expired(self):
        return time.time() > (self.__created_time + self.__life_time) if self.__life_time is not None else False
    
    def _update_data(self, data):
        self.__data = data
        self.__created_time = time.time()
    
    def data(self):
        if self.__data is not None and self.__is_expired():
            self.__data = None
        return self.__data

