from abc import ABC, abstractmethod


class ILogger(ABC):
    """Base class for logger"""

    @abstractmethod
    async def log_async(self, **kwargs):
        """log data async"""
