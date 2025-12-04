"""
Service Provider Interface - Dependency Injection Container Contract

Defines the contract for dependency injection containers in BasisCore.Edge.
Supports service registration, resolution, and lifecycle management.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from bclib.service_provider.service_lifetime import ServiceLifetime

T = TypeVar('T')


class IServiceProvider(ABC):
    """
    Dependency Injection Container Interface

    Defines the contract for DI containers that manage service registration,
    resolution, and lifecycle. Supports three lifetimes: singleton, scoped, and transient.

    Features:
        - Service registration with different lifetimes
        - Hosted services (instantiated at startup)
        - Constructor injection based on type hints
        - Method injection for handlers
        - Scoped services for request isolation
        - Async/sync handler support
    """

    @abstractmethod
    def add_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider'], T]] = None,
        instance: Optional[T] = None
    ) -> 'IServiceProvider':
        """
        Register a singleton service (one instance for entire application)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives IServiceProvider and creates the service
            instance: Pre-created instance

        Returns:
            Self for chaining
        """
        pass

    @abstractmethod
    def add_hosted(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider'], T]] = None,
        priority: int = 0
    ) -> 'IServiceProvider':
        """
        Register a hosted service (singleton instantiated at application startup)

        Hosted services are like singletons but are automatically instantiated
        when the listener starts, rather than lazily on first injection.
        Useful for background services, initializers, and startup tasks.

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives IServiceProvider and creates the service
            priority: Initialization priority (higher = initialized first, default=0)

        Returns:
            Self for chaining
        """
        pass

    @abstractmethod
    def add_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider'], T]] = None
    ) -> 'IServiceProvider':
        """
        Register a scoped service (one instance per request/scope)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives IServiceProvider and creates the service

        Returns:
            Self for chaining
        """
        pass

    @abstractmethod
    def add_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider'], T]] = None
    ) -> 'IServiceProvider':
        """
        Register a transient service (new instance every time)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives IServiceProvider and creates the service

        Returns:
            Self for chaining
        """
        pass

    @abstractmethod
    def get_service(self, service_type: Type[T], **kwargs: Any) -> Optional[T]:
        """
        Resolve and return a service instance

        Args:
            service_type: The service type to resolve
            **kwargs: Additional parameters for constructor injection

        Returns:
            Service instance or None if not registered
        """
        pass

    @abstractmethod
    def inject_dependencies(self, handler: Callable, **kwargs: Any) -> Dict[str, Any]:
        """
        Inject dependencies from DI container into handler parameters

        Args:
            handler: The handler function to inject dependencies into
            **kwargs: Keyword arguments already being passed (including url_segments)

        Returns:
            Dictionary of parameter names and resolved service instances
        """
        pass

    @abstractmethod
    def create_scope(self) -> 'IServiceProvider':
        """
        Create a new scope for scoped services (per-request)

        Returns:
            New IServiceProvider with same registrations but fresh scoped instances
        """
        pass

    @abstractmethod
    def clear_scope(self) -> None:
        """
        Clear scoped instances (call at end of request)

        Frees memory by removing scoped service instances.
        Singleton instances are preserved.
        """
        pass

    @abstractmethod
    def invoke_method(self, method: Callable, **kwargs: Any) -> Any:
        """
        Invoke a method with automatic dependency injection for its parameters

        Args:
            method: The method/function to invoke
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Method return value
        """
        pass

    @abstractmethod
    async def invoke_method_async(self, method: Callable, event_loop: Any, **kwargs: Any) -> Any:
        """
        Invoke an async method with automatic dependency injection

        Args:
            method: The async method/function to invoke
            event_loop: Event loop for running sync functions in executor
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Awaited method return value
        """
        pass

    @abstractmethod
    def invoke(self, method: Callable, event_loop: Any, **kwargs: Any) -> Any:
        """
        Smart invoke - automatically detects if method is async or sync

        Args:
            method: The method/function to invoke (sync or async)
            event_loop: Event loop for running async/sync methods
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Method return value (or coroutine for async methods)
        """
        pass

    @abstractmethod
    def create_instance(self, class_type: Type[T], **kwargs: Any) -> T:
        """
        Create an instance of a class with automatic dependency injection

        Args:
            class_type: The class to instantiate
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Instance with injected dependencies
        """
        pass

    @abstractmethod
    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered

        Args:
            service_type: The service type to check

        Returns:
            True if registered, False otherwise
        """
        pass

    @abstractmethod
    def get_lifetime(self, service_type: Type) -> Optional[ServiceLifetime]:
        """
        Get the lifetime of a registered service

        Args:
            service_type: The service type

        Returns:
            ServiceLifetime or None if not registered
        """
        pass

    @abstractmethod
    def remove_service(self, service_type: Type[T]) -> bool:
        """
        Remove a registered service from the container

        Args:
            service_type: The service type to remove

        Returns:
            True if service was removed, False if it wasn't registered

        Example:
            ```python
            services.add_singleton(ILogger, ConsoleLogger)
            services.remove_service(ILogger)  # Returns True
            services.remove_service(ILogger)  # Returns False (already removed)
            ```
        """
        pass

    @abstractmethod
    async def invoke_in_executor(self, method: Callable, event_loop: Any, **kwargs: Any) -> Any:
        """
        Invoke a method with DI, running sync methods in thread pool to avoid blocking

        Args:
            method: The method/function to invoke (sync or async)
            event_loop: The asyncio event loop for run_in_executor
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Awaited method return value
        """
        pass

    @abstractmethod
    async def initialize_hosted_services_async(self) -> None:
        """
        Initialize all hosted services by instantiating them and calling start_async

        This should be called at application startup (typically in dispatcher.initialize_task_async)
        to instantiate all services registered with add_hosted and call their start_async method
        if they implement IHostedService.
        """
        pass

    @abstractmethod
    async def stop_hosted_services_async(self) -> None:
        """
        Stop all hosted services by calling stop_async for graceful shutdown

        This should be called during application shutdown to call stop_async on all
        hosted services that implement IHostedService.
        """
        pass
