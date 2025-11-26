from abc import ABC, abstractmethod
from typing import Optional

from .log_object import LogObject


class ILogger(ABC):
    """
    Logger Interface

    Base interface for all logger implementations. Provides abstraction
    for logging mechanisms with support for async operations and log object creation.

    Implementations can log to various destinations:
        - RESTful APIs
        - RabbitMQ message queues
        - No-op (disabled logging)

    Example:
        ```python
        logger: ILogger = NoLogger()
        log_obj = logger.new_object_log("user_action", user_id=123, action="login")
        await logger.log_async(log_obj)
        ```
    """

    @abstractmethod
    async def log_async(self, log_object: LogObject):
        """
        Log data asynchronously

        Args:
            log_object: The log object containing schema name, routing key, and properties

        Raises:
            Exception: Implementation-specific exceptions during logging operation
        """

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
