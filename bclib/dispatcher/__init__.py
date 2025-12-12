from bclib.di import IServiceContainer

from .idispatcher import IDispatcher
from .imessage_handler import IMessageHandler


def adding_dispatcher_services(service_container: IServiceContainer) -> None:
    """
    Add Dispatcher services to the service provider

    This function registers the Dispatcher class and its related interfaces
    in the provided service provider (dependency injection container). It ensures
    that the Dispatcher can be resolved and used throughout the application.

    Args:
        service_provider: The IServiceProvider instance to register services with
    """
    from .dispatcher import Dispatcher

    # Register dispatcher itself in DI container
    service_container.add_singleton(Dispatcher, Dispatcher, is_hosted=True)
    service_container.add_singleton(
        IDispatcher, factory=lambda sp, **kwargs: sp.get_service(Dispatcher))
    service_container.add_singleton(
        IMessageHandler, factory=lambda sp, **kwargs: sp.get_service(Dispatcher))


__all__ = [
    'IDispatcher',
    'IMessageHandler',
    'adding_dispatcher_services',
]
