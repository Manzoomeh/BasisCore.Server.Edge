from abc import abstractmethod
from typing import Coroutine, Optional
from urllib.parse import urljoin

from bclib.log_service.ilog_service import ILogService
from bclib.log_service.log_object import LogObject
from bclib.log_service.log_schema import LogSchema


class SchemaBaseLogger(ILogService):
    """
    Schema-Based Logger Base Class

    Abstract base class for loggers that use schema definitions from a remote API.
    Handles schema loading, caching, and conversion of log objects to schema format.

    Subclasses must implement the `_save_schema_async` method to define how
    formatted schema data is persisted (e.g., REST API, RabbitMQ).

    Features:
        - Automatic schema loading from configured URL
        - Schema caching to reduce API calls
        - Conversion of LogObject to schema format
        - Error handling with logging

    Configuration:
        options must contain either:
            - 'url': Direct schema API URL
            - 'get_url': Schema API base URL

    Example:
        ```python
        class CustomLogger(SchemaBaseLogger):
            async def _save_schema_async(self, schema: dict, routing_key: str = None):
                # Implementation for saving schema
                pass
        ```
    """

    def __init__(self, options: dict) -> None:
        """
        Initialize schema-based logger

        Args:
            options: Logger configuration dictionary containing:
                - url or get_url: Schema API URL
                - Additional implementation-specific options

        Raises:
            Exception: If neither 'url' nor 'get_url' is configured
        """
        super().__init__()
        self.options = options
        if "url" in options:
            self.__get_url = options["url"]
        elif "get_url" in options:
            self.__get_url = options["get_url"]
        else:
            raise Exception(
                "url part of schema logger not set. set 'url' or 'get_url'")
        self.__schemas: 'dict[str,dict]' = dict()

    async def __load_schema_async(self, schema_name: str) -> LogSchema:
        """
        Load schema definition from API

        Args:
            schema_name: Name of the schema to load

        Returns:
            LogSchema: Loaded and parsed schema

        Raises:
            aiohttp exceptions: If API request fails
            KeyError: If schema response format is invalid
        """
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = urljoin(self.__get_url+"/", schema_name)
            async with session.get(url) as response:
                schema_source = await response.json()
                return LogSchema(schema_source["sources"][0]["data"][0])

    @abstractmethod
    async def _save_schema_async(self, schema: dict, routing_key: str = None):
        """
        Save formatted schema data (abstract method)

        Args:
            schema: Formatted schema data ready for persistence
            routing_key: Optional routing key for message-based loggers

        Note:
            Subclasses must implement this to define how schema
            data is persisted (e.g., POST to API, send to queue)
        """

    async def __get_dict_async(self, schema_name: int) -> LogSchema:
        """
        Get schema with caching

        Args:
            schema_name: Name of the schema to retrieve

        Returns:
            LogSchema: Cached or newly loaded schema

        Note:
            Schemas are cached after first load to reduce API calls
        """
        if schema_name not in self.__schemas:
            schema = await self.__load_schema_async(schema_name)
            self.__schemas[schema_name] = schema
        return self.__schemas[schema_name]

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> LogObject:
        """
        Create a new log object

        Args:
            schema_name: Name of the log schema to use
            routing_key: Optional routing key for message-based loggers (e.g., RabbitMQ)
            **kwargs: Property key-value pairs to include in the log

        Returns:
            LogObject: Configured log object ready for logging

        Example:
            ```python
            log_obj = logger.new_object_log(
                "user_activity",
                routing_key="users.login",
                user_id=123,
                ip_address="192.168.1.1"
            )
            ```
        """
        return LogObject(schema_name, routing_key, **kwargs)

    async def log_async(self, log_object: LogObject = None, **kwargs):
        """
        Log data asynchronously using schema

        Loads the schema (with caching), converts log properties to
        schema format, and saves via the implementation-specific method.

        Args:
            log_object: Log object containing schema name and properties.
                       If None, creates from kwargs (requires 'schema_name' in kwargs)
            **kwargs: Log parameters for creating log object if log_object is None

        Raises:
            Exception: If schema_name not provided when log_object is None

        Note:
            Errors are caught and printed to console without raising.
            This prevents logging failures from breaking application flow.
        """
        if log_object is None:
            if "schema_name" not in kwargs:
                raise Exception("'schema_name' not set for apply logging!")
            schema_name = kwargs.pop("schema_name")
            log_object = self.new_object_log(schema_name, **kwargs)

        try:
            questions = await self.__get_dict_async(
                schema_name=log_object.schema_name
            )
            answer = questions.get_answer(
                params=log_object.properties
            )
            await self._save_schema_async(answer, log_object.routingKey)
        except Exception as ex:
            print(
                f"Error in log with schema logger: {repr(ex)}")

    def log_in_background(self, log_object: LogObject = None, **kwargs) -> Coroutine:
        """
        Log in background process

        Args:
            log_object: Pre-created log object. If None, creates from kwargs
            **kwargs: Log parameters

        Returns:
            Coroutine: Task for background logging
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.create_task(self.log_async(log_object, **kwargs))
