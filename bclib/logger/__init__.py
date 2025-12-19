"""Logger Module

Provides independent generic logger functionality based on Python's standard logging.
"""
from bclib.di import IServiceContainer

from .ilogger import ILogger

__all__ = [
    'ILogger'
]


def add_default_logger(service_container: IServiceContainer) -> None:
    """
    Register Logger Services in DI Container

    Adds ConsoleLogger as the implementation for ILogger[T] in the service provider.
    Configures loggers based on provided AppOptions.

    Args:
        services: The service provider to register services with
        options: Application options containing logger configuration

    Example:
        ```python
        from bclib import edge
        from bclib.logger import add_logger_services
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Load app options (e.g., from config file)
        app_options = edge.load_app_options("config/host.json")

        # Register logger services
        add_logger_services(services, app_options)

        # Now ILogger[T] can be injected in handlers
        ```
    """
    from .console_logger import ConsoleLogger
    service_container.add_singleton(ILogger, implementation=ConsoleLogger)
