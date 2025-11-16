"""
Injection Strategy - Strategy pattern for parameter resolution

Defines different strategies for resolving handler parameters:
- ValueStrategy: Extract value with optional type conversion (for URL segments)
- ServiceStrategy: Resolve from DI container
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Type

if TYPE_CHECKING:
    from .service_provider import ServiceProvider


class InjectionStrategy(ABC):
    """Base class for parameter injection strategies"""

    @abstractmethod
    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> any:
        """Resolve parameter value from ServiceProvider and kwargs"""
        pass


class ValueStrategy(InjectionStrategy):
    """Inject value with optional type conversion (typically from URL segments)"""

    def __init__(self, param_name: str, target_type: Type = str) -> None:
        self.param_name: str = param_name
        self.target_type: Type = target_type

    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> Optional[any]:
        # Get value directly from kwargs
        value = kwargs.get(self.param_name)

        if value is None:
            return None

        # Type conversion
        if self.target_type in (int, float):
            try:
                return self.target_type(value)
            except (ValueError, TypeError):
                return None

        return value


class ServiceStrategy(InjectionStrategy):
    """Inject from DI container"""

    def __init__(self, service_type: Type) -> None:
        self.service_type: Type = service_type

    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> Optional[any]:
        if services is None:
            return None

        return services.get_service(self.service_type, **kwargs)
