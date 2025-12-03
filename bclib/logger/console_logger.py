"""Generic Console Logger

Independent generic logger module based on Python's standard logging module.
Creates typed logger instances that write to console.
"""
import logging
from typing import Generic, Optional, Type, TypeVar

from bclib.app_options import AppOptions
from bclib.logger.ilogger import ILogger

T = TypeVar('T')


class ConsoleLogger(ILogger[T]):
    """
    Generic Console Logger

    Independent generic logger that creates typed logger instances using Python's
    standard logging module. Configures loggers based on AppOptions and writes to console.

    Type Parameters:
        T: The type identifier for the logger (used for type safety and naming)

    Configuration:
        AppOptions should contain 'logger' key with:
            - name: Logger name (optional, defaults to class name T)
            - level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            - format: Log message format (optional)

    Example:
        ```python
        # Define a type for your logger context
        class UserService:
            pass

        # Create logger configuration
        options = {
            'logger': {
                'name': 'UserService',
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

        # Create typed logger
        logger = ConsoleLogger[UserService](options)

        # Use the logger
        logger.info("User logged in", user_id=123)
        logger.error("Login failed", error="Invalid credentials")
        logger.debug("Processing request", data={"key": "value"})

        # Without configuration (uses defaults)
        default_logger = ConsoleLogger[UserService]({})
        default_logger.info("Using default configuration")
        ```
    """

    _DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    _DEFAULT_LEVEL = logging.INFO

    def __init__(self, options: AppOptions, generic_type_args: tuple[Type, ...] = None):
        """
        Initialize generic application logger

        Args:
            options: Application configuration containing logger settings
            logger_type: Optional type hint for the logger (used for naming)
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

        self.__type_hint = generic_type_args
        self._configure_logger(options)

    def _configure_logger(self, options: AppOptions) -> None:
        """
        Configure logger with handlers and formatters

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

            # Create formatter
            log_format = logger_config.get('format', self._DEFAULT_FORMAT)
            formatter = logging.Formatter(log_format)
            console_handler.setFormatter(formatter)

            # Add handler to logger
            self.addHandler(console_handler)

    # All logging methods (debug, info, warning, error, critical, exception)
    # are inherited from logging.Logger base class

    def __repr__(self) -> str:
        """String representation of ConsoleLogger"""
        type_name = self.__type_hint.__name__ if self.__type_hint else "Generic"
        return f"ConsoleLogger[{type_name}](name='{self.name}', level={logging.getLevelName(self.level)})"
