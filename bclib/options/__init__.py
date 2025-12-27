"""Options module - Configuration access for dependency injection"""

from bclib.di import IServiceContainer

from .app_options import AppOptions
from .ioptions import IOptions

__all__ = ['IOptions', 'add_options_service']


def add_options_service(service_container: IServiceContainer, app_options: dict) -> IServiceContainer:
    """
    Register IOptions in DI container

    Args:
        service_container: IServiceContainer instance
        app_options: Application options dictionary

    Note:
        IOptions is registered as transient because each injection needs
        a different configuration key based on the generic type parameter.
    """
    from bclib.di import IServiceProvider

    def create_options(sp: IServiceProvider, **kwargs):
        """Factory for creating Options with configuration key"""
        from bclib.di import extract_generic_type_key
        from bclib.utility import resolve_dict_value

        from .service_options import ServiceOptions

        app_options = sp.get_service(AppOptions)
        key = extract_generic_type_key(kwargs)
        options = resolve_dict_value(key, app_options)
        return ServiceOptions(options)

    return service_container\
        .add_singleton(AppOptions, instance=app_options)\
        .add_transient(IOptions, factory=create_options)
