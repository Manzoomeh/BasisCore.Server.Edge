from abc import ABC, abstractproperty
from utility import DictEx
from .db_manager import DbManager, SqlDb, SQLiteDb, MongoDb, RabbitConnection, RESTfulConnection


class Context(ABC):
    """Base class for dispatching"""

    def __init__(self, options: DictEx) -> None:
        super().__init__()
        self._options = options
        self.__db_manager = DbManager(options)
        self.url_segments = None

    @abstractproperty
    @property
    def url(self) -> str:
        pass

    def open_sql_connection(self, key: str) -> SqlDb:
        return self.__db_manager.open_sql_connection(key)

    def open_sqllite_connection(self, key: str) -> SQLiteDb:
        return self.__db_manager.open_sqllite_connection(key)

    def open_mongo_connection(self, key: str) -> MongoDb:
        return self.__db_manager.open_mongo_connection(key)

    def open_restful_connection(self, key: str) -> RESTfulConnection:
        return self.__db_manager.open_restful_connection(key)

    def open_rabbit_connection(self, key: str) -> RabbitConnection:
        return self.__db_manager.open_rabbit_connection(key)
