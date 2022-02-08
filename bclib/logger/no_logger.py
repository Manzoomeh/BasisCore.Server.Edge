from ..logger.ilogger import ILogger


class NoLogger(ILogger):
    """class for no logging"""

    async def log_async(self, **kwargs):
        """log data async"""
