from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple

from bclib.exception import ShortCircuitErr

if TYPE_CHECKING:
    from .. import dispatcher

from bclib.db_manager import SqlDb, SQLiteDb, MongoDb, RabbitConnection, RESTfulConnection
from bclib.utility import DictEx, HttpStatusCodes


class Context(ABC):
    """Base class for dispatching"""

    def __init__(self, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__()
        self.dispatcher = dispatcher
        self.url_segments: DictEx = None
        self.url: str = None
        self.is_adhoc = True

    def open_sql_connection(self, key: str) -> SqlDb:
        return self.dispatcher.db_manager.open_sql_connection(key)

    def open_sqllite_connection(self, key: str) -> SQLiteDb:
        return self.dispatcher.db_manager.open_sqllite_connection(key)

    def open_mongo_connection(self, key: str) -> MongoDb:
        return self.dispatcher.db_manager.open_mongo_connection(key)

    def open_restful_connection(self, key: str) -> RESTfulConnection:
        return self.dispatcher.db_manager.open_restful_connection(key)

    def open_rabbit_connection(self, key: str) -> RabbitConnection:
        return self.dispatcher.db_manager.open_rabbit_connection(key)

    def generate_error_response(self, exception: Exception) -> dict:
        """Generate error response from process result"""

        error_object, _ = self._generate_error_object(exception)
        return error_object

    def _generate_error_object(self, exception: Exception) -> 'Tuple[dict, HttpStatusCodes]':
        """Generate error object from exception object"""
        error_code = None
        status_code = HttpStatusCodes.INTERNAL_SERVER_ERROR
        if isinstance(exception, ShortCircuitErr):
            status_code = exception.status_code
            error_code = exception.error_code
        error_object = {
            "errorCode": error_code,
            "errorMessage": str(exception)
        }

        return (error_object, status_code)
