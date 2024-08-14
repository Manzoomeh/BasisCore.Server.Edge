from abc import ABC, abstractmethod
from .log_object import LogObject
from .log_object import LogObject

class ILogger(ABC):
    """Base class for logger"""

    @abstractmethod
    async def log_async(self, log_object: LogObject):
    async def log_async(self, log_object: LogObject):
        """log data async"""

    def new_object_log(self, schema_name: str, **kwargs) -> LogObject:
        """New object log"""
        return LogObject(schema_name, **kwargs)