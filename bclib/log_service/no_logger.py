from bclib.log_service.ilogger import ILogger
from bclib.log_service.log_object import LogObject


class NoLogger(ILogger):
    """
    No-Operation Logger

    Logger implementation that discards all log data. Used when
    logging is disabled or not configured.

    This is a null object pattern implementation that provides
    the ILogger interface without performing any actual logging operations.

    Example:
        ```python
        logger = NoLogger()
        log_obj = logger.new_object_log("test", data="value")
        await logger.log_async(log_obj)  # Does nothing
        ```
    """

    async def log_async(self, log_object: LogObject):
        """
        Log data asynchronously (no-op)

        Args:
            log_object: The log object to discard

        Note:
            This method does nothing and returns immediately.
        """
