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
    from .iservice_provider import IServiceProvider


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
        factory: Optional[Callable[['IServiceProvider', Any], Any]] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        is_hosted: bool = False,
        priority: int = 0
    ) -> None:
        """
        Initialize service descriptor

        Args:
            service_type: The interface or abstract type to register
            implementation: Concrete implementation type (will be instantiated)
            factory: Factory function that receives ServiceProvider and **kwargs, returns an instance
            instance: Pre-created instance (for singletons)
            lifetime: Service lifetime (singleton/scoped/transient)
            is_hosted: Whether service should be instantiated at application startup
            priority: Initialization priority for hosted services (higher = initialized first, default=0)
        """
        self.service_type: Type = service_type
        self.implementation: Optional[Type] = implementation
        self.factory: Optional[Callable[[
            'IServiceProvider', Any], Any]] = factory
        self.instance: Optional[Any] = instance
        self.lifetime: ServiceLifetime = lifetime
        self.is_hosted: bool = is_hosted
        self.priority: int = priority
