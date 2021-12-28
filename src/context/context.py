from abc import ABC, abstractproperty
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import dispatcher
from .db_manager import DbManager, SqlDb, SQLiteDb, MongoDb, RabbitConnection, RESTfulConnection


class Context(ABC):
    """Base class for dispatching"""

    def __init__(self, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__()
        self._dispateher = dispatcher
        self.__db_manager = DbManager(dispatcher.options)
        self.url_segments = None

    @property
    def dispatcher(self) -> 'dispatcher.IDispatcher':
        return self._dispateher

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
