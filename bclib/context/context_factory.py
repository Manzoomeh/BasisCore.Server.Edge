"""Context Factory - Creates appropriate context instances from messages"""
from typing import TYPE_CHECKING, Optional, Type

from bclib.logger.ilogger import ILogger
from bclib.options.app_options import AppOptions

if TYPE_CHECKING:
    from bclib.predicate.url import Url

    from .context import Context

from bclib.dispatcher.callback_info import CallbackInfo
from bclib.dispatcher.idispatcher import IDispatcher
from bclib.listener.http.http_message import HttpMessage
from bclib.listener.http.websocket_message import WebSocketMessage
from bclib.listener.icms_base_message import ICmsBaseMessage
from bclib.listener.message import Message
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
        dispatcher: IDispatcher,
        options: AppOptions,
        logger: ILogger['ContextFactory'],
        lookup: dict[Type, list[CallbackInfo]]
    ):
        """
        Initialize ContextFactory

        Args:
            dispatcher: Dispatcher instance for context creation
            options: Dispatcher options containing router configuration
            logger: Logger instance for request logging
            lookup: Handler lookup dictionary
        """
        self.__logger = logger
        self.__dispatcher = dispatcher
        self.__options = options
        self.__look_up = lookup

        # Extract logging configuration from options
        self.__log_request = options.get('log_request', True)
        name = options.get('name')
        self.__log_name = f"{name}: " if name else ''

        # Routing configuration
        # pattern -> (Url predicate or None for '*', context_type)
        self.__route_lookup: dict[str, tuple[Optional['Url'], Type['Context']]] = {}

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
            method = req.get('methode', req.get('method', 'none'))

        # Determine context type based on URL patterns or message type
        # 1. Try to match URL patterns in lookup (prefer concrete patterns over '*').
        #    Patterns are matched against the whole request path, segment by segment,
        #    exactly as the Url predicate matches it during dispatch.
        if url is not None and self.__route_lookup:
            path = ContextFactory._path_of(url)
            wildcard_type = None
            for pattern, (url_predicate, ctx_type) in self.__route_lookup.items():
                if url_predicate is None:
                    wildcard_type = ctx_type
                    continue
                if url_predicate.is_match(path):
                    context_type = ctx_type
                    break
            if context_type is None and wildcard_type is not None:
                context_type = wildcard_type

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
            self.__logger.info(log_msg)

        # Instantiate the context
        ret_val = context_type(cms_object, self.__dispatcher, message)

        return ret_val

    @staticmethod
    def _path_of(full_url: str) -> str:
        """Return the request path of a CMS full-url ('host[:port]/path?query' -> 'path')"""
        path = full_url.split('?', 1)[0].split('#', 1)[0]
        if '://' in path:
            path = path.split('://', 1)[1]
        # The first segment is the host (with optional port)
        return path.split('/', 1)[1] if '/' in path else ''

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

        # Collect all URL predicates per context type (None = any path)
        context_patterns: dict[Type['Context'], list[Optional['Url']]] = {}

        for ctx_type, handlers in self.__look_up.items():
            if ctx_type not in supported_contexts or len(handlers) == 0:
                continue

            context_patterns[ctx_type] = []

            # Extract URL predicates from each callback info
            for callback_info in handlers:
                url_predicates = callback_info.get_url_predicates()
                # No URL restriction -> this context type handles any path
                context_patterns[ctx_type].extend(url_predicates or [None])

        # Build lookup dictionary from all patterns
        self.__route_lookup = {}
        for context_type, url_predicates in context_patterns.items():
            for url_predicate in url_predicates:
                pattern = "*" if url_predicate is None else url_predicate.expression
                self.__route_lookup[pattern] = (url_predicate, context_type)
