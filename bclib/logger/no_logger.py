from bclib.logger.log_object import LogObject
from ..logger.ilogger import ILogger


class NoLogger(ILogger):
    """class for no logging"""

    async def log_async(self, log_object: LogObject):
        """log data async"""