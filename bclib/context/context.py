import base64
import traceback
from abc import ABC
from typing import TYPE_CHECKING, Optional, Tuple, Type, TypeVar

from bclib.db_manager import (MongoDb, RabbitConnection, RESTfulConnection,
                              SqlDb, SQLiteDb)
from bclib.exception import ShortCircuitErr
from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType
from bclib.service_provider import ServiceProvider
from bclib.utility import DictEx, HttpStatusCodes

if TYPE_CHECKING:
    from .. import dispatcher

T = TypeVar('T')


class Context(ABC):
    """Base class for dispatching"""

    def __init__(self, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__()
        self.dispatcher = dispatcher
        self.url_segments: dict = None
        self.url: str = None
        self.is_adhoc = True

        # Create scoped service provider for this request
        self.__service_provider: ServiceProvider = dispatcher.create_scope()
        # Register current context as singleton in the scoped service provider
        self.__service_provider.add_singleton(type(self), instance=self)

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

    @property
    def services(self) -> ServiceProvider:
        """
        Get scoped service provider for this request

        Returns:
            ServiceProvider instance with scoped services for this request

        Example:
            ```python
            @app.restful_action()
            async def my_handler(context: RESTfulContext):
                logger = context.get_service(ILogger)
                db = context.get_service(IDatabase)

                logger.log("Processing request...")
                await db.query("SELECT * FROM users")
            ```
        """
        return self.__service_provider

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Convenience method to get a service from the DI container

        Args:
            service_type: The type of service to resolve

        Returns:
            Service instance or None if not registered

        Example:
            ```python
            logger = context.get_service(ILogger)
            if logger:
                logger.log("Hello from DI!")
            ```
        """
        # Flatten url_segments into kwargs for service resolution
        kwargs = self.url_segments if self.url_segments else {}

        return self.__service_provider.get_service(service_type, **kwargs)

    def generate_error_response(self, exception: Exception) -> dict:
        """Generate error response from process result"""

        error_object, _ = self._generate_error_object(exception)
        return error_object

    def _generate_error_object(self, exception: Exception) -> 'Tuple[dict, str]':
        """Generate error object from exception object"""
        error_code = None
        data = None
        status_code = HttpStatusCodes.INTERNAL_SERVER_ERROR
        if isinstance(exception, ShortCircuitErr):
            data = exception.data
            status_code = exception.status_code
            error_code = exception.error_code
        if data:
            error_object = data
        else:
            error_object = {
                "errorCode": error_code,
                "errorMessage": str(exception)
            }
            if self.dispatcher.log_error:
                error_object["error"] = traceback.format_exc()
        return (error_object, status_code)

    @staticmethod
    def _generate_response_cms(
            content: 'str|bytes',
            response_type: 'str',
            status_code: 'str',
            mime: 'str',
            template: 'DictEx' = None,
            headers: 'dict' = None) -> dict:
        """Generate response from process result"""

        ret_val = DictEx() if template is None else template
        if HttpBaseDataType.CMS not in ret_val:
            ret_val[HttpBaseDataType.CMS] = {}
        if HttpBaseDataName.WEB_SERVER not in ret_val[HttpBaseDataType.CMS]:
            ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER] = DictEx()
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.INDEX] = response_type
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.HEADER_CODE] = status_code
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.MIME] = mime
        if isinstance(content, bytes):
            ret_val[HttpBaseDataType.CMS][HttpBaseDataName.BLOB_CONTENT] = content
        else:
            ret_val[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT] = content
        if headers is not None:
            Context.__add_user_defined_headers(ret_val, headers)
        return ret_val

    @staticmethod
    def __add_user_defined_headers(response: dict, headers: dict) -> None:
        """Adding user defined header to response"""

        if HttpBaseDataName.HTTP not in response[HttpBaseDataType.CMS]:
            response[HttpBaseDataType.CMS][HttpBaseDataName.HTTP] = {}
        http = response[HttpBaseDataType.CMS][HttpBaseDataName.HTTP]
        for key, value in headers.items():
            if key in http:
                current_value = http[key] if isinstance(
                    http[key], list) else [http[key]]
                new_value = current_value + value
            else:
                new_value = value

            http[key] = ",".join(new_value)
