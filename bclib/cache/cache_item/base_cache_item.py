from abc import ABC, abstractmethod
from datetime import datetime, timedelta

class BaseCacheItem(ABC):
    def __init__(self, data:"any", life_time:"int"=0) -> None:
        self._data = data
        self.__life_time = timedelta(seconds=life_time) if life_time > 0 else None
        self.__expiration = self.__set_expiration()

    def __set_expiration(self) -> "datetime|None":
        return datetime.utcnow() + self.__life_time if self.__life_time else None

    # @abstractmethod
    # def get_data(self, *args, **kwargs) -> "any|None":
    #     if self._data is not None and self.is_expired:
    #         self._data = None

    @property
    def data(self) -> "any":
        return self._data

    @property
    def is_expired(self) -> "bool":
        return datetime.utcnow() > self.__expiration if self.__expiration else False

    def update_data(self, data:"any"):
        self._data = data
        self.__expiration = self.__set_expiration()