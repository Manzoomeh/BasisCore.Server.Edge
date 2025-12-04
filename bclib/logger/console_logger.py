"""Generic Console Logger

Independent generic logger module based on Python's standard logging module.
Creates typed logger instances that write to console with color support and async logging.
"""
import atexit
import logging
import logging.handlers
import queue
import sys
from typing import Generic, Optional, Type, TypeVar

from bclib.app_options import AppOptions
from bclib.logger.ilogger import ILogger

T = TypeVar('T')


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'  # Gray for timestamp

    def __init__(self, fmt: str, use_colors: bool = True):
        """
        Initialize colored formatter

        Args:
            fmt: Log message format
            use_colors: Whether to use colors (default: True)
        """
        super().__init__(fmt)
        self.use_colors = use_colors and self._supports_color()

    @staticmethod
    def _supports_color() -> bool:
        """Check if the terminal supports colors"""
        # Check if stdout is a TTY and not redirected
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False
        # Windows 10+ supports ANSI colors
        if sys.platform == 'win32':
            try:
                import os

                # Enable ANSI escape sequences on Windows
                os.system('')
                return True
            except:
                return False
        return True

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        if self.use_colors:
            # Save original values
            levelname = record.levelname
            asctime = self.formatTime(record, self.datefmt)

            # Add color to level name
            if levelname in self.COLORS:
                record.levelname = f"{self.BOLD}{self.COLORS[levelname]}{levelname}{self.RESET}"

            # Format the message
            result = super().format(record)

            # Add gray color to timestamp (if timestamp is in the format)
            if '%(asctime)s' in self._fmt or '%(asctime)' in self._style._fmt:
                # Replace timestamp with gray colored version
                result = result.replace(
                    asctime, f"{self.GRAY}{asctime}{self.RESET}", 1)

            # Reset levelname for next use
            record.levelname = levelname
            return result
        else:
            return super().format(record)


class ConsoleLogger(ILogger[T]):
    """
    Generic Console Logger with Color Support and Async Logging

    Independent generic logger that creates typed logger instances using Python's
    standard logging module. Configures loggers based on AppOptions and writes to console
    with color-coded output for different log levels.

    Features asynchronous logging using QueueHandler to prevent I/O blocking on the main thread,
    which significantly improves performance in high-traffic applications.

    Type Parameters:
        T: The type identifier for the logger (used for type safety and naming)

    Configuration:
        AppOptions should contain 'logger' key with:
            - name: Logger name (optional, defaults to class name T)
            - level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            - format: Log message format (optional)
            - use_colors: Enable/disable colors (optional, default: True)
            - async_logging: Enable/disable async logging (optional, default: True)
            - queue_size: Max queue size for async logging (optional, default: -1 for unlimited)

    Color Scheme:
        - DEBUG: Cyan
        - INFO: Green
        - WARNING: Yellow
        - ERROR: Red
        - CRITICAL: Magenta
        - Timestamp: Gray

    Performance:
        - Async logging moves I/O operations to a background thread
        - Main thread only puts log records in a queue (very fast)
        - No blocking on console writes
        - Automatic cleanup on application exit

    Example:
        ```python
        # Define a type for your logger context
        class UserService:
            pass

        # Create logger configuration with async logging
        options = {
            'logger': {
                'name': 'UserService',
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'use_colors': True,
                'async_logging': True,  # Enable async logging for better performance
                'queue_size': -1  # Unlimited queue (default)
            }
        }

        # Create typed logger
        logger = ConsoleLogger[UserService](options)

        # Use the logger (non-blocking, output will be colored)
        logger.info("User logged in", user_id=123)        # Green (async)
        logger.warning("Slow query detected")             # Yellow (async)
        logger.error("Login failed", error="timeout")     # Red (async)

        # Disable async logging if needed (for debugging)
        options['logger']['async_logging'] = False
        sync_logger = ConsoleLogger[UserService](options)
        ```
    """

    _DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    _DEFAULT_LEVEL = logging.INFO

    def __init__(self, options: AppOptions, generic_type_args: tuple[Type, ...] = None):
        """
        Initialize generic application logger with color support and async logging

        Args:
            options: Application configuration containing logger settings
            generic_type_args: Optional type arguments for the logger (used for naming)
        """
        # Determine logger name
        logger_config = options.get('logger', {})
        if 'name' in logger_config:
            logger_name = logger_config['name']
        elif generic_type_args is not None and len(generic_type_args) > 0:
            logger_name = generic_type_args[0].__name__
        else:
            logger_name = 'ConsoleLogger'

        # Initialize base logger
        super().__init__(logger_name)

        self.__type_hint = generic_type_args[0] if generic_type_args and len(
            generic_type_args) > 0 else None
        self.__queue_listener: Optional[logging.handlers.QueueListener] = None
        self._configure_logger(options)

    def _configure_logger(self, options: AppOptions) -> None:
        """
        Configure logger with colored console handler and async logging support

        Args:
            options: Application configuration
        """
        logger_config = options.get('logger', {})

        # Set logging level
        level_name = logger_config.get('level', 'INFO').upper()
        level = getattr(logging, level_name, self._DEFAULT_LEVEL)
        self.setLevel(level)

        # Check if handler already exists (avoid duplicate handlers)
        if not self.handlers:
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Create colored formatter
            log_format = logger_config.get('format', self._DEFAULT_FORMAT)
            use_colors = logger_config.get('use_colors', True)
            formatter = ColoredFormatter(log_format, use_colors=use_colors)
            console_handler.setFormatter(formatter)

            # Check if async logging is enabled (default: True)
            async_logging = logger_config.get('async_logging', True)

            if async_logging:
                # Create queue for async logging
                queue_size = logger_config.get(
                    'queue_size', -1)  # -1 = unlimited
                log_queue = queue.Queue(maxsize=queue_size)

                # Create queue handler (fast, non-blocking)
                queue_handler = logging.handlers.QueueHandler(log_queue)
                self.addHandler(queue_handler)

                # Create queue listener (processes logs in background thread)
                self.__queue_listener = logging.handlers.QueueListener(
                    log_queue,
                    console_handler,
                    respect_handler_level=True
                )
                self.__queue_listener.start()

                # Register cleanup on exit
                atexit.register(self._cleanup)
            else:
                # Synchronous logging (direct to console)
                self.addHandler(console_handler)

    def _cleanup(self) -> None:
        """Clean up queue listener on exit"""
        if self.__queue_listener is not None:
            self.__queue_listener.stop()
            self.__queue_listener = None

    def __del__(self):
        """Destructor to ensure cleanup"""
        self._cleanup()

    # All logging methods (debug, info, warning, error, critical, exception)
    # are inherited from logging.Logger base class

    def __repr__(self) -> str:
        """String representation of ConsoleLogger"""
        type_name = self.__type_hint.__name__ if self.__type_hint else "Generic"
        return f"ConsoleLogger[{type_name}](name='{self.name}', level={logging.getLevelName(self.level)})"
