"""Log Service Implementation"""
import asyncio
from typing import Coroutine, Optional

from bclib.app_options import AppOptions
from bclib.log_service.ilog_service import ILogService
from bclib.log_service.ilogger import ILogger
from bclib.log_service.log_object import LogObject
from bclib.log_service.no_logger import NoLogger
from bclib.log_service.rabbit_schema_base_logger import RabbitSchemaBaseLogger
from bclib.log_service.restful_schema_base_logger import \
    RESTfulSchemaBaseLogger


class LogService(ILogService):
    """
    Logging service implementation

    Provides logging functionality with support for async operations
    and background task execution. Includes built-in logger factory logic
    to create appropriate logger instances based on configuration.

    Supported logger types:
        - schema.restful: RESTful API-based logging
        - schema.rabbit: RabbitMQ-based logging
        - None: NoLogger (no logging)

    Example:
        ```python
        @app.restful_handler(app.url("api/process"))
        async def handler(log_service: ILogService):
            # Create and log
            log_obj = log_service.new_object_log("user_action", user_id=123)
            await log_service.log_async(log_obj)

            # Or log in background
            log_service.log_in_background(schema_name="background_task", data="test")
        ```
    """

    def __init__(self, options: AppOptions, loop: asyncio.AbstractEventLoop):
        """
        Initialize log service

        Args:
            options: Application configuration (AppOptions type alias for dict)
            loop: The asyncio event loop for async operations
        """
        # Create logger based on configuration (integrated factory logic)
        self.__logger: ILogger = self.__create_logger(options)
        self.__log_error: bool = options.get('log_error', False)
        self.__log_request: bool = options.get('log_request', True)
        self.__event_loop = loop

    @staticmethod
    def __create_logger(options: AppOptions) -> ILogger:
        """
        Create a logger instance based on configuration (factory method)

        Args:
            options: Application configuration (AppOptions type alias for dict)

        Returns:
            ILogger: Configured logger instance

        Raises:
            Exception: If logger type is not specified or not supported
        """
        logger: ILogger = None
        if "logger" not in options:
            logger = NoLogger()
        else:
            logger_option: AppOptions = options.get('logger')
            if 'type' not in logger_option:
                raise Exception("Type property not set for logger!")
            else:
                logger_type = logger_option.get('type').lower()
                if logger_type == 'schema.restful':
                    logger = RESTfulSchemaBaseLogger(logger_option)
                elif logger_type == "schema.rabbit":
                    logger = RabbitSchemaBaseLogger(logger_option)
                else:
                    raise Exception(
                        f"Type '{logger_type}' not support for logger")
            print(f'{logger.__class__.__name__} start logging')
        return logger

    @property
    def log_error(self) -> bool:
        """Get log error setting"""
        return self.__log_error

    @property
    def log_request(self) -> bool:
        """Get log request setting"""
        return self.__log_request

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> LogObject:
        """
        Create a new log object

        Args:
            schema_name: Schema name for the log
            routing_key: Optional routing key for message routing
            **kwargs: Additional log parameters

        Returns:
            LogObject: New log object instance
        """
        return self.__logger.new_object_log(schema_name, routing_key, **kwargs)

    async def log_async(self, log_object: LogObject = None, **kwargs):
        """
        Log asynchronously

        Args:
            log_object: Pre-created log object. If None, creates from kwargs
            **kwargs: Log parameters including 'schema_name' (required if log_object is None)

        Raises:
            Exception: If schema_name not provided when log_object is None
        """
        if log_object is None:
            if "schema_name" not in kwargs:
                raise Exception("'schema_name' not set for apply logging!")
            schema_name = kwargs.pop("schema_name")
            log_object = self.new_object_log(schema_name, **kwargs)
        await self.__logger.log_async(log_object)

    def log_in_background(self, log_object: LogObject = None, **kwargs) -> Coroutine:
        """
        Log in background process

        Args:
            log_object: Pre-created log object. If None, creates from kwargs
            **kwargs: Log parameters

        Returns:
            Coroutine: Task for background logging
        """
        return self.__event_loop.create_task(
            self.log_async(log_object, **kwargs)
        )
