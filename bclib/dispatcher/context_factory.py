"""Context Factory - Creates appropriate context instances from messages"""
import json
import re
from struct import error
from typing import TYPE_CHECKING, Callable, Optional, Type

from bclib.app_options import AppOptions

if TYPE_CHECKING:
    from bclib.context import (ClientSourceContext, Context, HttpContext,
                               RabbitContext, RESTfulContext, ServerSourceContext,
                               WebSocketContext)
    from bclib.dispatcher import IDispatcher

from bclib.dispatcher.callback_info import CallbackInfo
from bclib.listener import HttpBaseDataType, Message, MessageType
from bclib.listener.http.http_message import HttpMessage
from bclib.listener.http.websocket_message import WebSocketMessage
from bclib.listener.icms_base_message import ICmsBaseMessage
from bclib.listener.rabbit.rabbit_message import RabbitMessage
from bclib.listener.tcp.tcp_message import TcpMessage


class ContextFactory:
    """
    Factory class for creating appropriate context instances from messages

    This factory examines incoming messages and creates the correct context type
    (RESTful, WebSocket, Socket, etc.) based on message properties and routing configuration.

    Attributes:
        dispatcher: Reference to the dispatcher instance
        context_type_lookup: Dictionary mapping URL patterns to context types
        log_request: Whether to log incoming requests
        log_name: Name to use in log messages
    """

    def __init__(
        self,
        dispatcher: 'IDispatcher',
        options: AppOptions,
        lookup: dict[Type, list[CallbackInfo]]
    ):
        """
        Initialize ContextFactory

        Args:
            dispatcher: Dispatcher instance for context creation
            options: Dispatcher options containing router configuration
            lookup: Handler lookup dictionary
        """
        self.__dispatcher = dispatcher
        self.__options = options
        self.__look_up = lookup

        # Extract logging configuration from options
        self.__log_request = options.get('log_request', True)
        name = options.get('name')
        self.__log_name = f"{name}: " if name else ''

        # Routing configuration
        # pattern -> context_type
        self.__route_lookup: dict[str, Type['Context']] = {}

    def create_context(self, message: Message) -> 'Context':
        """
        Create appropriate context type from message

        Analyzes the message type, content, and URL to determine which context
        type should be created (RESTful, WebSocket, Socket, etc.)

        Args:
            message: The incoming message to create context from

        Returns:
            Context: Appropriate context instance for the message

        Raises:
            KeyError: If required fields are missing from CMS object
            NameError: If context type cannot be determined or is invalid
        """
        ret_val: Context = None
        context_type = None
        cms_object: Optional[dict] = None
        url: Optional[str] = None
        request_id: Optional[str] = None
        method: Optional[str] = None
        message_json: Optional[dict] = None

        # Extract CMS object from message
        if isinstance(message, ICmsBaseMessage):
            cms_object = message.cms_object["cms"]

        # Extract request metadata from CMS object
        if cms_object:
            if 'request' in cms_object:
                req = cms_object["request"]
            else:
                raise KeyError("request key not found in cms object")

            if 'full-url' in req:
                url = req["full-url"]
            else:
                raise KeyError("full-url key not found in request")

            request_id = dict.get(req, 'request-id', 'none')
            method = dict.get(req, 'method', 'none')

        # Determine context type based on URL patterns or message type
        # 1. Try to match URL patterns in lookup
        if url and self.__route_lookup:
            for pattern, ctx_type in self.__route_lookup.items():
                if pattern == "*" or re.search(pattern, url):
                    context_type = ctx_type
                    break

        # 2. Fallback to message type if no match found
        if context_type is None:
            # Import context types at runtime to avoid circular dependency
            from bclib.context import (HttpContext, RabbitContext,
                                       WebSocketContext)

            if isinstance(message, HttpMessage) or isinstance(message, TcpMessage):
                context_type = HttpContext
            elif isinstance(message, WebSocketMessage):
                context_type = WebSocketContext
            elif isinstance(message, RabbitMessage):
                context_type = RabbitContext

        # Create appropriate context instance
        if context_type is None:
            raise NameError(f"No context found for '{url}'")

        # Log request if enabled
        if self.__log_request:
            context_name = context_type.__name__ if context_type else "Unknown"
            log_msg = f"{self.__log_name}({context_name}::{message.type.name})"
            if cms_object:
                log_msg += f" - {request_id} {method} {url}"
            print(log_msg)

        # Instantiate the context
        ret_val = context_type(cms_object, self.__dispatcher, message)

        return ret_val

    def rebuild_router(self):
        """Auto-generate router from registered handlers in lookup"""
        # Import context types at runtime to avoid circular dependency
        from bclib.context import (ClientSourceContext, HttpContext,
                                   RESTfulContext, ServerSourceContext,
                                   WebSocketContext)

        # Supported context types
        supported_contexts = {
            RESTfulContext,
            HttpContext,
            WebSocketContext,
            ClientSourceContext,
            ServerSourceContext
        }

        # Collect all URL patterns per context type
        context_patterns: dict[Type[Context], list[str]] = {}

        for ctx_type, handlers in self.__look_up.items():
            if ctx_type not in supported_contexts or len(handlers) == 0:
                continue

            context_patterns[ctx_type] = []

            # Extract URL patterns from each callback info
            for callback_info in handlers:
                patterns = callback_info.get_url_patterns()
                context_patterns[ctx_type].extend(patterns)

        # Build lookup dictionary from all patterns
        self.__route_lookup = {}
        for context_type, patterns in context_patterns.items():
            for pattern in patterns:
                self.__route_lookup[pattern] = context_type
