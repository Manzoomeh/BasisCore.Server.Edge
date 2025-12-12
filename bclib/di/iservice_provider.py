"""
Service Provider Interface - Dependency Injection Service Resolution Contract

Defines the contract for service resolution and dependency injection at runtime.
Separated from IServiceContainer to enforce clear separation of concerns:
- IServiceContainer: Registration and configuration (setup phase)
- IServiceProvider: Resolution and injection (runtime phase)
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar('T')


class IServiceProvider(ABC):
    """
    Service Resolution and Dependency Injection Interface

    Provides runtime service resolution and dependency injection capabilities.
    Does NOT include registration methods - use IServiceContainer for setup.

    This separation ensures:
    - Code receiving IServiceProvider cannot modify container configuration
    - Clear distinction between setup phase and runtime phase
    - Better dependency inversion principle adherence

    Features:
        - Service resolution with automatic dependency injection
        - Constructor injection based on type hints
        - Method injection for handlers
        - Scoped services for request isolation
        - Async/sync handler support
    """

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
