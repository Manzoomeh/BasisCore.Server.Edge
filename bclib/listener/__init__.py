
from typing import TYPE_CHECKING, Any, Optional, Type

if TYPE_CHECKING:
    from bclib.di.iservice_provider import IServiceProvider

from bclib.utility.http_base_data_name import HttpBaseDataName
from bclib.utility.http_base_data_type import HttpBaseDataType

from .endpoint import Endpoint
from .http.http_listener import HttpListener
from .http.http_message import HttpMessage
from .http.iwebsocket_session_manager import IWebSocketSessionManager
from .http.websocket_message import WebSocketMessage, WSMessageType
from .http.websocket_session import WebSocketSession
from .http.websocket_session_manager import WebSocketSessionManager
from .icms_base_message import ICmsBaseMessage
from .ilistener import IListener
from .ilistener_factory import IListenerFactory
from .iresponse_base_message import IResponseBaseMessage
from .listener_factory import ListenerFactory
from .message import Message
from .message_type import MessageType
from .rabbit.rabbit_message import RabbitMessage
from .tcp.tcp_listener import TcpListener
from .tcp.tcp_message import TcpMessage


def adding_listener_services(service_provider: 'IServiceProvider'):
    """Add listener services to the service provider for dependency injection.

    This function registers all listener-related classes and interfaces with the
    provided service provider, enabling dependency injection throughout the application.

    Args:
        service_provider: The service provider instance to which listener services
                          will be added.
    """
    service_provider.add_transient(
        IListenerFactory, ListenerFactory)
    service_provider.add_singleton(IWebSocketSessionManager,
                                   WebSocketSessionManager)
    pass
