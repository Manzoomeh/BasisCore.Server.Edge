"""Log Service Module

Provides logging service for application-wide logging functionality.
"""

from bclib.service_provider.iservice_provider import IServiceProvider

from .ilog_service import ILogService
from .log_object import LogObject
from .log_service import LogService

__all__ = ['ILogService', 'LogService', 'LogObject']


def add_log_service(service_provider: IServiceProvider) -> None:
    """
    Register Log Service in DI Container

    Adds LogService as the implementation for ILogService in the service provider.

    Args:
        service_provider: The service provider to register services with

    Example:
        ```python
        from bclib import edge
        from bclib.log_service import add_log_service
        from bclib.service_provider import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register log service
        add_log_service(services)

        # Now ILogService can be injected in handlers
        ```
    """

    service_provider.add_singleton(ILogService, LogService)
