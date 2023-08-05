from bclib.utility import DictEx
from ..time_logger.base_time_logger import BaseTimeLogger

class NoTimeLogger(BaseTimeLogger):
    def __init__(self, options: "DictEx") -> None:
        super().__init__(options)

    def log_async(self):
        """
        No log
        """

    
