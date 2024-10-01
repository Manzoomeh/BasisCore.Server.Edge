from abc import ABC, abstractmethod
from .log_object import LogObject
from typing import Optional

class ILogger(ABC):
    """Base class for logger"""

    @abstractmethod
    async def log_async(self, log_object: LogObject):
        """log data async"""

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> LogObject:
        """New object log"""
        return LogObject(schema_name, routing_key, **kwargs)
