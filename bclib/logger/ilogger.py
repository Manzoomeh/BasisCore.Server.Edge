from abc import ABC, abstractmethod
from bclib.utility import DictEx

class ILogger(ABC):
    """Base class for logger"""
    def __init__(self, options:"DictEx") -> None:
        super().__init__()
        self.name = options.name
        
    @abstractmethod
    async def log_async(self, **kwargs):
        """log data async"""
