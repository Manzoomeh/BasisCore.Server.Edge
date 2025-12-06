"""
Context - Base class for all request contexts

This module provides the base Context class for the BasisCore.Server.Edge framework.
All protocol-specific contexts (HTTP, WebSocket, TCP, etc.) inherit from this base class
to provide common functionality including dependency injection, service provider access,
and error response generation.

Key Features:
    - Scoped dependency injection per request
    - Service provider pattern for accessing registered services
    - Automatic context registration in DI container
    - Base error handling and response generation
    - Protocol-agnostic request abstraction

Example:
    ```python
    # Using context in a handler
    @app.restful_handler(app.url("api/users"))
    async def get_users(context: RESTfulContext):
        # Access dependency injection services
        db = context.services.get_service(IDatabase)
        logger = context.services.get_service(ILogger)
        
        # Use services
        logger.info("Fetching users...")
        users = await db.query("SELECT * FROM users")
        
        return {"users": users}
    ```
    
Note:
    This is an abstract base class. Use protocol-specific contexts like
    RESTfulContext, HttpContext, WebSocketContext, or TcpContext in your handlers.
"""
from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.service_provider.iservice_provider import IServiceProvider


class Context(ABC):
    """
    Base class for all request contexts

    Provides foundational functionality for request handling including dependency injection,
    service provider access, and error response generation. All protocol-specific contexts
    inherit from this class.

    Attributes:
        dispatcher (IDispatcher): The dispatcher instance handling this request
        services (IServiceProvider): Scoped service provider for dependency injection

    Args:
        dispatcher: Dispatcher instance managing routing and handlers
        create_scope: Whether to create a new DI scope for this request
                     (True for request-scoped services, False to use parent scope)

    Example:
        ```python
        # Context is automatically created by the framework
        # You receive it as the first parameter in handlers

        @app.http_action(app.url("api/health"))
        async def health_check(context: HttpContext):
            # context is automatically injected
            return {"status": "healthy"}
        ```

    Note:
        When create_scope=True, the context registers itself as a singleton
        in its own scope, allowing services to depend on the current context.
    """

    def __init__(self, dispatcher: 'IDispatcher', create_scope: bool) -> None:
        """
        Initialize the base context

        Args:
            dispatcher: Dispatcher instance for routing and DI container access
            create_scope: If True, creates a new DI scope; if False, uses parent scope

        Note:
            Most request contexts use create_scope=True to isolate request-level services.
            Member contexts (like ClientSourceMemberContext) may use False to share
            the parent context's scope.
        """
        super().__init__()
        self.dispatcher = dispatcher

        # Create scoped service provider for this request
        if create_scope:
            self.__service_provider = dispatcher.service_provider.create_scope()
            # Register current context as singleton in the scoped service provider
            self.__service_provider.add_singleton(type(self), instance=self)
        else:
            self.__service_provider = dispatcher.service_provider

    @property
    def services(self) -> 'IServiceProvider':
        """
        Get scoped service provider for this request

        Provides access to the dependency injection container for retrieving
        registered services. Services are resolved based on their registration
        lifetime (singleton, scoped, or transient).

        Returns:
            IServiceProvider: Service provider instance with access to all registered services

        Example:
            ```python
            @app.restful_handler(app.url("api/users"))
            async def get_users(context: RESTfulContext):
                # Get services by interface type
                logger = context.services.get_service(ILogger)
                db = context.services.get_service(IDatabase)
                cache = context.services.get_service(ICacheManager)

                # Use the services
                logger.info("Fetching users from database...")
                users = await db.query("SELECT * FROM users")

                return {"users": users}
            ```

        Note:
            Scoped services are created once per request and shared across
            all service dependencies within the same request context.
        """
        return self.__service_provider

    def generate_error_response(self, exception: Exception) -> dict:
        """
        Generate error response from exception

        Converts an exception into a standardized error response format.
        Override this method in derived classes to customize error formatting
        for specific protocols (e.g., JSON for REST, HTML for web pages).

        Args:
            exception: The exception that occurred during request processing

        Returns:
            dict: Error response object with errorCode and errorMessage fields

        Example:
            ```python
            # Default error response format:
            {
                "errorCode": None,
                "errorMessage": "Division by zero"
            }

            # Override in derived class for custom formatting:
            class MyContext(Context):
                def generate_error_response(self, exception: Exception) -> dict:
                    return {
                        "error": {
                            "type": type(exception).__name__,
                            "message": str(exception),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
            ```

        Note:
            RESTfulContext and HttpContext override this to set appropriate
            HTTP status codes based on exception type.
        """
        return {
            "errorCode": None,
            "errorMessage": str(exception)
        }
