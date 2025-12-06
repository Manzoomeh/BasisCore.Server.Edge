"""Logger Module

Provides independent generic logger functionality based on Python's standard logging.
"""

from bclib.logger.console_logger import ConsoleLogger
from bclib.logger.ilogger import ILogger

__all__ = [
    'ConsoleLogger',
    'ILogger'
]
