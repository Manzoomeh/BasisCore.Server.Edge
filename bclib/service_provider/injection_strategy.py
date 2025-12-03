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


class ServiceStrategy(InjectionStrategy):
    """Inject from DI container"""

    def __init__(self, service_type: Type) -> None:
        self.service_type: Type = service_type

    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> Optional[any]:
        if services is None:
            return None

        return services.get_service(self.service_type, **kwargs)


class GenericServiceStrategy(InjectionStrategy):
    """Inject generic types from DI container

    Handles parameterized generic types like ILogger[T], Repository[User], etc.
    Extracts the base generic type and type arguments to resolve the appropriate
    service from the container. The type arguments are passed to the service
    constructor/factory via kwargs.

    Example:
        For ILogger["MyApp"], extracts:
        - generic_type: ILogger
        - type_args: ("MyApp",)

        Then calls: services.get_service(ILogger, generic_type_args=("MyApp",))
    """

    def __init__(self, param_type: Type) -> None:
        """
        Initialize strategy for generic type

        Args:
            param_type: The full generic type (e.g., ILogger["MyApp"])
        """
        self.param_type: Type = param_type
        self.generic_origin: Optional[Type] = get_origin(param_type)
        self.type_args: tuple = get_args(param_type)

    def resolve(self, services: 'ServiceProvider', **kwargs: Any) -> Optional[any]:
        """
        Resolve generic service from container

        Tries to resolve using the base generic type and passes type arguments
        via kwargs so they can be used in constructor or factory function.

        Args:
            services: Service provider instance
            **kwargs: Additional resolution parameters

        Returns:
            Resolved service instance or None
        """
        if services is None:
            return None

        # Prepare kwargs with generic type arguments
        service_kwargs = kwargs.copy()
        if self.type_args:
            service_kwargs['generic_type_args'] = self.type_args

        # Try to get service with generic origin (base type)
        if self.generic_origin is not None:
            service = services.get_service(
                self.generic_origin, **service_kwargs)
            if service is not None:
                return service

        # Fallback: try with full generic type
        return services.get_service(self.param_type, **service_kwargs)
