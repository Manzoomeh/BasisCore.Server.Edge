"""Options module - Configuration access for dependency injection"""
from typing import ForwardRef

from bclib.service_provider.iservice_provider import IServiceProvider

from .app_options import AppOptions
from .ioptions import IOptions
from .service_options import ServiceOptions

__all__ = ['IOptions', 'service_options', 'add_options_service']


def add_options_service(service_provider: IServiceProvider, app_options: dict):
    """
    Register IOptions in DI container

    Args:
        service_provider: ServiceProvider instance
        app_options: Application options dictionary

    Note:
        IOptions is registered as transient because each injection needs
        a different configuration key based on the generic type parameter.
    """
    def create_options(sp: IServiceProvider, **kwargs):
        """Factory for creating Options with configuration key"""
        app_options = sp.get_service(AppOptions)
        type_args: tuple[type, ...] = kwargs.get(
            'generic_type_args', ('',))
        key: str = None

        # Extract class name from ForwardRef or type
        key_source = type_args[0]

        if isinstance(key_source, ForwardRef):
            # ForwardRef: extract the string representation
            key = key_source.__forward_arg__
        elif isinstance(key_source, type):
            # Actual class: use __name__
            key = key_source.__name__
        elif isinstance(key_source, str):
            # Already a string
            key = key_source
        else:
            # Fallback to string representation
            key = str(key_source)

        return ServiceOptions(key, app_options)

    service_provider.add_singleton(AppOptions, instance=app_options)
    service_provider.add_transient(IOptions, factory=create_options)
