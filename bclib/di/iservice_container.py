"""
Service Container Interface - Contract for DI container registration and management

Defines the contract for registering services and managing the DI container.
Separated from IServiceProvider to distinguish between container setup (registration)
and service resolution (runtime).
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional, Type, TypeVar

from .service_lifetime import ServiceLifetime

T = TypeVar('T')


class IServiceContainer(ABC):
    """
    Interface for Dependency Injection Container Registration and Management

    This interface defines methods for registering services and managing
    the DI container configuration. It's separated from IServiceProvider to
    distinguish between:
    - Container setup phase (registration, configuration)
    - Runtime phase (service resolution, dependency injection)

    Typical usage:
    - Use IServiceContainer during application startup to register services
    - Use IServiceProvider during runtime to resolve services and inject dependencies
    """

    @abstractmethod
    def add_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider'], T]] = None,
        instance: Optional[T] = None,
        is_hosted: bool = False,
        priority: int = 0
    ) -> 'IServiceContainer':
        """
        Register a singleton service (one instance for entire application)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives IServiceProvider and creates the service
            instance: Pre-created instance
            is_hosted: If True, service is instantiated at startup and start_async is called
            priority: Initialization priority for hosted services (higher = initialized first, default=0)

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
    ) -> 'IServiceContainer':
        """
        Register a scoped service (one instance per scope/request)

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
    ) -> 'IServiceContainer':
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
        """
        pass

    @abstractmethod
    async def initialize_hosted_services_async(self) -> None:
        """
        Initialize all hosted services by instantiating them and calling start_async

        This should be called at application startup (typically in dispatcher.initialize_task_async)
        to instantiate all services registered with add_singleton(is_hosted=True) and call their start_async method
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
