"""Log Service Interface"""
from abc import ABC, abstractmethod
from typing import Coroutine, Optional

from bclib.log_service.log_object import LogObject


class ILogService(ABC):
    """
    Interface for logging service

    Provides methods for creating and managing log objects with support
    for both synchronous and asynchronous logging.
    """

    @property
    def log_error(self) -> bool:
        """
        Get log error setting

        Returns:
            bool: True if error logging is enabled (default: False)
        """
        return False

    @property
    def log_request(self) -> bool:
        """
        Get log request setting

        Returns:
            bool: True if request logging is enabled (default: True)
        """
        return True

    @abstractmethod
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
        pass

    @abstractmethod
    async def log_async(self, log_object: LogObject = None, **kwargs):
        """
        Log asynchronously

        Args:
            log_object: Pre-created log object. If None, creates from kwargs
            **kwargs: Log parameters including 'schema_name' (required if log_object is None)

        Raises:
            Exception: If schema_name not provided when log_object is None
        """
        pass

    @abstractmethod
    def log_in_background(self, log_object: LogObject = None, **kwargs) -> Coroutine:
        """
        Log in background process

        Args:
            log_object: Pre-created log object. If None, creates from kwargs
            **kwargs: Log parameters

        Returns:
            Coroutine: Task for background logging
        """
        pass
