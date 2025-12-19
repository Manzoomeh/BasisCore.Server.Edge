
from bclib.di import IServiceContainer

from .endpoint import Endpoint
from .icms_base_message import ICmsBaseMessage
from .ilistener import IListener
from .ilistener_factory import IListenerFactory
from .iresponse_base_message import IResponseBaseMessage
from .message import Message
from .message_type import MessageType

__all__ = ['Endpoint',
           'ICmsBaseMessage', 'IListener', 'IListenerFactory',
           'IResponseBaseMessage', 'Message', 'MessageType']


def adding_listener_services(service_container: IServiceContainer) -> None:
    """Add listener services to the service provider for dependency injection.

    This function registers all listener-related classes and interfaces with the
    provided service provider, enabling dependency injection throughout the application.

    Args:
        service_container: The service container instance to which listener services
                          will be added.
    """
    from .http import IWebSocketSessionManager, WebSocketSessionManager
    from .listener_factory import ListenerFactory

    return service_container\
        .add_transient(IListenerFactory, ListenerFactory)\
        .add_singleton(IWebSocketSessionManager, WebSocketSessionManager)
