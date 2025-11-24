"""Context Factory - Creates appropriate context instances from messages"""
import json
import re
from struct import error
from typing import TYPE_CHECKING, Callable, Optional, Type

from bclib.context import (ClientSourceContext, Context, RabbitContext,
                           RequestContext, RESTfulContext, ServerSourceContext,
                           WebContext, WebSocketContext)
from bclib.dispatcher.callback_info import CallbackInfo
from bclib.listener import HttpBaseDataType, Message, MessageType
from bclib.listener.http_listener.http_message import HttpMessage
from bclib.listener.http_listener.websocket_message import WebSocketMessage
from bclib.listener.icms_base_message import ICmsBaseMessage

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher


class ContextFactory:
    """
    Factory class for creating appropriate context instances from messages

    This factory examines incoming messages and creates the correct context type
    (RESTful, WebSocket, Socket, etc.) based on message properties and routing configuration.

    Attributes:
        dispatcher: Reference to the dispatcher instance
        context_type_detector: Callable that detects context type from URL
        default_router: Default context type when URL-based detection fails
        log_request: Whether to log incoming requests
        log_name: Name to use in log messages
    """

    def __init__(
        self,
        dispatcher: 'IDispatcher',
        options: dict,
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
        self.__context_type_detector: Optional[Callable[[str], str]] = None
        self.__context_type_lookup = None
        self.__manual_router_config = False  # Track if router was manually configured

        # Configure router from options
        if 'router' in options:
            self.__manual_router_config = True
            router = options['router']
            if isinstance(router, str):
                self.__context_type_detector: Callable[[
                    str], str] = lambda _: router
            elif isinstance(router, dict):
                self.__init_router_lookup(router)
            else:
                raise error(
                    "Invalid value for 'router' property in host options! Use string or dict object only.")
        else:
            self.__build_router_from_lookup()

    def create_context(self, message: Message) -> Context:
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
        ret_val: RequestContext = None
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

        # Determine context type based on message type and URL

        context_type = self.__context_type_detector(
            url) if self.__context_type_detector else None

        # Log request if enabled
        if self.__log_request:
            log_msg = f"{self.__log_name}({context_type}::{message.type.name})"
            if cms_object:
                log_msg += f" - {request_id} {method} {url}"
            print(log_msg)

        # Create appropriate context instance
        if context_type == "client_source":
            ret_val = ClientSourceContext(
                cms_object, self.__dispatcher, message)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms_object, self.__dispatcher, message)
        elif context_type == "server_source":
            ret_val = ServerSourceContext(message_json, self.__dispatcher)
        elif context_type == "web":
            ret_val = WebContext(cms_object, self.__dispatcher, message)
        elif context_type == "websocket":
            ret_val = WebSocketContext(cms_object, self.__dispatcher, message)
        elif context_type is None:
            raise NameError(f"No context found for '{url}'")
        else:
            raise NameError(
                f"Configured context type '{context_type}' not found for '{url}'")

        return ret_val

    def ensure_router_initialized(self):
        """Ensure router is initialized before message processing"""
        if self.__context_type_detector is None:
            self.__build_router_from_lookup()

    def rebuild_router_if_needed(self):
        """Rebuild router if auto-generated"""
        if not self.__manual_router_config:
            self.__build_router_from_lookup()

    def __build_router_from_lookup(self):
        """Auto-generate router from registered handlers in lookup"""
        from bclib.predicate.url import Url

        # Map context types to router names
        context_to_router = {
            RESTfulContext: "restful",
            WebContext: "web",
            WebSocketContext: "websocket",
            ClientSourceContext: "client_source",
            ServerSourceContext: "server_source"
        }

        # Collect all URL patterns per context type
        context_patterns = {}

        for ctx_type, handlers in self.__look_up.items():
            if ctx_type not in context_to_router or len(handlers) == 0:
                continue

            context_name = context_to_router[ctx_type]
            context_patterns[context_name] = []

            # Extract URL patterns from predicates
            for callback_info in handlers:
                predicates = callback_info._CallbackInfo__predicates
                for predicate in predicates:
                    if isinstance(predicate, Url):
                        pattern = predicate.exprossion
                        regex_pattern = re.sub(
                            r':(\w+)', r'(?P<\1>[^/]+)', pattern)
                        context_patterns[context_name].append(regex_pattern)

        available_contexts = list(context_patterns.keys())

        if len(available_contexts) == 1:
            default = available_contexts[0]
            self.__context_type_detector: Callable[[
                str], str] = lambda _: default
        else:
            route_lookup = []
            for context_name, patterns in context_patterns.items():
                for pattern in patterns:
                    route_lookup.append((pattern, context_name))
            self.__context_type_lookup = route_lookup
            self.__context_type_detector = self.__context_type_detect_from_lookup

    def __init_router_lookup(self, router_config: dict):
        """Initialize router lookup dictionary from configuration"""
        route_dict = {}
        for key, values in router_config.items():
            if '*' in values:
                route_dict['*'] = key
                break
            else:
                for value in values:
                    if len(value.strip()) != 0 and value not in route_dict:
                        route_dict[value] = key
            if len(route_dict) == 1 and '*' in route_dict:
                router = route_dict['*']
                self.__context_type_detector: Callable[[
                    str], str] = lambda _: router
            else:
                self.__context_type_lookup = route_dict.items()
                self.__context_type_detector = self.__context_type_detect_from_lookup

    def __context_type_detect_from_lookup(self, url: str) -> str:
        """Detect context type from URL using lookup patterns"""
        context_type: str = None
        if url:
            try:
                for pattern, lookup_context_type in self.__context_type_lookup:
                    if pattern == "*" or re.search(pattern, url):
                        context_type = lookup_context_type
                        break
            except TypeError:
                pass
            except error as ex:
                print("Error in detect context from routing options!", ex)
        return context_type

    @property
    def context_type_detector(self) -> Optional[Callable[[str], str]]:
        """Get the context type detector function"""
        return self.__context_type_detector
