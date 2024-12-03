from bclib.utility import DictEx
from .log_object import LogObject
from .ilogger import ILogger


class NoLogger(ILogger):
    """class for no logging"""

    def __init__(self,options:'DictEx'):
        super().__init__(options)

    async def log_async(self, log_object: LogObject):
        """log data async"""