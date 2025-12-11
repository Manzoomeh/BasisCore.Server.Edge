"""
Injection Strategy - Strategy pattern for parameter resolution

Defines different strategies for resolving handler parameters:
- ValueStrategy: Extract value with optional type conversion (for URL segments)
- ServiceStrategy: Resolve from DI container
- GenericServiceStrategy: Resolve generic types from DI container
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Type, get_args, get_origin

if TYPE_CHECKING:
    from .service_provider import ServiceProvider


class InjectionStrategy(ABC):
    """Base class for parameter injection strategies"""

    @abstractmethod
    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> any:
        """Resolve parameter value from ServiceProvider and kwargs"""
        pass


class ValueStrategy(InjectionStrategy):
    """Inject value with optional type conversion (typically from URL segments)

    First checks kwargs for the parameter value, then applies optional type conversion.
    Base class for other strategies that need kwargs lookup.

    Supports conversion for: str, int, float, list, tuple, set
    """

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

        # Handle list type conversion
        elif self.target_type == list:
            if isinstance(value, list):
                return value
            elif isinstance(value, (tuple, set)):
                return list(value)
            else:
                return [value]

        # Handle tuple type conversion
        elif self.target_type == tuple:
            if isinstance(value, tuple):
                return value
            elif isinstance(value, (list, set)):
                return tuple(value)
            else:
                return (value,)

        # Handle set type conversion
        elif self.target_type == set:
            if isinstance(value, set):
                return value
            elif isinstance(value, (list, tuple)):
                return set(value)
            else:
                return {value}

        return value


class ServiceStrategy(ValueStrategy):
    """Inject from DI container or kwargs

    First checks if the parameter is provided in kwargs (via parent ValueStrategy),
    then falls back to DI container. This allows explicit parameter overrides while 
    still supporting dependency injection.

    IMPORTANT: kwargs are NOT passed to nested dependencies to avoid parameter name conflicts.
    Only the root-level injection receives kwargs.
    """

    def __init__(self, param_name: str, service_type: Type) -> None:
        # target_type not used, set to object
        super().__init__(param_name, target_type=service_type)

    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> Optional[any]:
        # First, check if value is explicitly provided in kwargs
        if self.param_name in kwargs:
            return kwargs[self.param_name]

        # Fall back to DI container - DO NOT pass kwargs to avoid nested parameter conflicts
        # Example: HttpListener has 'options' for HTTP config, ILogger also has 'options' for app config
        # We don't want HttpListener's options to interfere with ILogger's options
        if services is None:
            return None

        return services.get_service(self.target_type)
