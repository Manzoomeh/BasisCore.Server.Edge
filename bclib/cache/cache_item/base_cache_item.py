from abc import ABC
import time

class BaseCacheItem(ABC):
    def __init__(self, data:"any", life_time:"int") -> None:
        super().__init__()
        self.__data = data
        self.__life_time = life_time
        self.__created_time = time.time()

    def __is_expired(self):
        return time.time() > (self.__created_time + self.__life_time) if self.__life_time > 0 else False
    
    def _update_data(self, data):
        self.__data = data
        self.__created_time = time.time()
    
    def data(self):
        if self.__data is not None and self.__is_expired():
            self.__data = None
        return self.__data

