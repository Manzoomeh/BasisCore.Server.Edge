"""
Service Descriptor - Describes how a service should be created

Contains the configuration for service registration including:
- Service type (interface)
- Implementation type
- Factory function
- Pre-created instance
- Service lifetime
"""
from typing import TYPE_CHECKING, Any, Callable, Optional, Type

from .service_lifetime import ServiceLifetime

if TYPE_CHECKING:
    from .service_provider import ServiceProvider


class ServiceDescriptor:
    """
    Describes how a service should be created and managed

    A service can be registered in three ways:
    1. Implementation type: ServiceProvider will instantiate it
    2. Factory function: Custom creation logic (receives ServiceProvider)
    3. Instance: Pre-created instance (singleton only)
    """

    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable[['ServiceProvider'], Any]] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> None:
        """
        Initialize service descriptor

        Args:
            service_type: The interface or abstract type to register
            implementation: Concrete implementation type (will be instantiated)
            factory: Factory function that returns an instance
            instance: Pre-created instance (for singletons)
            lifetime: Service lifetime (singleton/scoped/transient)
        """
        self.service_type: Type = service_type
        self.implementation: Optional[Type] = implementation
        self.factory: Optional[Callable] = factory
        self.instance: Optional[Any] = instance
        self.lifetime: ServiceLifetime = lifetime
