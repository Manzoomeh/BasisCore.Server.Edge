"""
Injection Plan - Pre-compiled injection plan for performance

Analyzes handler/class signature once at decoration time and creates
optimized injection strategies for each parameter.

This eliminates the need for reflection on every request, significantly
improving performance in high-traffic scenarios.

Can be used for:
- Method/function execution with automatic DI
- Class instantiation with constructor injection
"""
import asyncio
import inspect
import traceback
from typing import (TYPE_CHECKING, Any, Callable, Coroutine, Dict, ForwardRef,
                    Type, Union, get_args, get_origin, get_type_hints)

from .injection_strategy import (InjectionStrategy, ServiceStrategy,
                                 ValueStrategy)

if TYPE_CHECKING:
    from .service_provider import ServiceProvider


class InjectionPlan:
    """
    Pre-compiled injection plan for a handler or class

    Analyzes signature once at creation time and creates
    optimized injection strategies for each parameter.

    NEW: List Type Support for Multiple Implementations
    ----------------------------------------------------
    Now automatically detects and injects list[Type] parameters with all
    registered implementations from the DI container.

    Can be used for:
    - Method/function calls with automatic DI
    - Class instantiation with constructor injection
    - Automatic injection of multiple service implementations

    Example:
        ```python
        # Class with list parameter
        class NotificationManager:
            def __init__(self, services: list[INotificationService]):
                self.services = services  # Auto-injected with all implementations

        # Register multiple implementations
        container.add_singleton(INotificationService, EmailService)
        container.add_singleton(INotificationService, SmsService)
        container.add_singleton(INotificationService, PushService)

        # Create instance - automatically injects all three services
        plan = InjectionPlan(NotificationManager)
        manager = plan.create_instance(container)
        # manager.services = [EmailService, SmsService, PushService]
        ```
    """

    def __init__(self, target: Union[Callable, Type]) -> None:
        """
        Initialize injection plan for a callable or class

        Args:
            target: Either a function/method or a class to analyze
        """
        self.target: Union[Callable, Type] = target
        self.is_class: bool = inspect.isclass(target)
        self.is_async: bool = False if self.is_class else inspect.iscoroutinefunction(
            target)
        self.param_strategies: Dict[str, InjectionStrategy] = {}
        self.has_value_parameters: bool = False  # Optimization flag
        self._analyze()

    def _analyze(self) -> None:
        """Analyze target signature once and build injection strategies

        Handles various type annotation formats:
        - Regular types: int, str, MyClass
        - String annotations: "MyClass" (from __future__ annotations or forward refs)
        - ForwardRef: ForwardRef('MyClass')
        - Generic types: IOptions['database'], ILogger['App']
        - String generic types: "IOptions['database']" (from __future__ annotations)
        """
        try:
            # Get the right callable to analyze
            if self.is_class:
                # For classes, analyze __init__
                callable_to_analyze = self.target.__init__
            else:
                # For functions/methods, analyze directly
                callable_to_analyze = self.target

            sig = inspect.signature(callable_to_analyze)

            # Try to get type hints with proper resolution
            try:
                type_hints = get_type_hints(callable_to_analyze)
            except (NameError, AttributeError) as hint_error:
                # If get_type_hints fails (e.g., forward references in TYPE_CHECKING),
                # fall back to __annotations__ (string annotations won't be resolved)
                type_hints = getattr(callable_to_analyze,
                                     '__annotations__', {})

            for param_name, param in sig.parameters.items():
                # Skip 'self' parameter for class constructors
                if param_name == 'self':
                    continue

                param_type = type_hints.get(param_name)

                if param_type is None:
                    continue

                # Handle string annotations (from __future__ annotations or forward refs)
                # These can be simple ("MyClass") or complex ("IOptions['database']")
                if isinstance(param_type, str):
                    # String annotation - could be simple type or generic type expression
                    # For generic types like "IOptions['database']", we need to evaluate it
                    # But since evaluation might fail due to undefined names in the string,
                    # we treat all string annotations as service types
                    # ServiceProvider will handle the resolution
                    self.param_strategies[param_name] = ServiceStrategy(
                        param_name, param_type)
                    continue

                # Handle ForwardRef (from generic types like IOptions['database'])
                if isinstance(param_type, ForwardRef):
                    # ForwardRef contains the original type - pass it as-is
                    # ServiceProvider will extract the string via __forward_arg__
                    self.param_strategies[param_name] = ServiceStrategy(
                        param_name, param_type)
                    continue

                # Check if it's a primitive type or Optional[primitive]
                actual_type = param_type

                # Handle Optional types (Union[X, None])
                origin = get_origin(param_type)
                if origin is Union:
                    args = get_args(param_type)
                    # Check if it's Optional (Union with None)
                    if type(None) in args:
                        # Get the non-None type
                        actual_type = next(
                            (arg for arg in args if arg is not type(None)), None)
                        origin = get_origin(
                            actual_type) if actual_type else None

                # Check if it's a primitive type that could be URL segment
                if actual_type in (str, int, float, list, tuple, set):
                    self.param_strategies[param_name] = ValueStrategy(
                        param_name, actual_type)
                    self.has_value_parameters = True  # Mark that we need kwargs
                # Check if origin is a collection type (List, Tuple, Set)
                elif origin in (list, tuple, set):
                    # Check if the collection contains service types or primitives
                    # This enables automatic injection of multiple implementations
                    args = get_args(param_type)
                    if args and args[0] not in (str, int, float, bool, bytes):
                        # Collection of service types - use ServiceStrategy
                        # This triggers ServiceProvider.get_service(list[Type])
                        # which returns all registered implementations
                        # Example: list[INotificationService], list[IListener]
                        #
                        # Usage:
                        #   class Manager:
                        #       def __init__(self, listeners: list[IListener]):
                        #           # Auto-injected with all IListener implementations
                        #           self.listeners = listeners
                        self.param_strategies[param_name] = ServiceStrategy(
                            param_name, param_type)
                    else:
                        # Collection of primitives - use ValueStrategy for URL segments
                        # These are passed via kwargs (e.g., from URL path parameters)
                        # Example: list[str], list[int]
                        self.param_strategies[param_name] = ValueStrategy(
                            param_name, origin)
                        self.has_value_parameters = True  # Mark that we need kwargs
                else:
                    # Assume it's a service type (both regular and generic types)
                    # get_service() handles generic type resolution automatically
                    # This includes types like ILogger['App'], IOptions['database']
                    self.param_strategies[param_name] = ServiceStrategy(
                        param_name, param_type)

        except Exception as ex:
            # If analysis fails, fall back to empty strategies
            print(f"InjectionPlan analysis failed: {ex}")
            raise ex

    def inject_parameters(self, services: 'ServiceProvider', **kwargs: Any) -> Dict[str, Any]:
        """
        Execute injection plan (fast - no reflection)

        Args:
            services: ServiceProvider instance for DI
            **kwargs: Additional values (e.g., url_segments flattened)

        Returns:
            Dictionary of parameter names to resolved values
        """
        result: Dict[str, Any] = {}

        for param_name, strategy in self.param_strategies.items():
            try:
                value = strategy.resolve(services, **kwargs)
                if value is not None:
                    result[param_name] = value
            except Exception as ex:
                print(
                    f"Failed to resolve parameter '{param_name}' for {self.target}: {ex}")
                traceback.print_exc()

        return result

    def create_instance(self, services: 'ServiceProvider', *args: Any, **kwargs: Any) -> Any:
        """
        Create instance of a class with injected dependencies

        Args:
            services: ServiceProvider instance for DI
            *args: Positional arguments to pass to constructor
            **kwargs: Keyword arguments to pass to constructor (including url_segments)

        Returns:
            New instance with injected dependencies

        Example:
            ```python
            class MyService:
                def __init__(self, logger: ILogger, db: IDatabase):
                    self.logger = logger
                    self.db = db

            plan = InjectionPlan(MyService)
            instance = plan.create_instance(services)
            ```
        """
        if not self.is_class:
            raise TypeError(f"{self.target} is not a class")

        injected_kwargs = self.inject_parameters(services, **kwargs)

        return self.target(*args, **injected_kwargs)

    def execute_async(self, services: 'ServiceProvider', event_loop: 'asyncio.AbstractEventLoop', *args: Any, **kwargs: Any) -> Union[Coroutine, Any]:
        """
        Execute handler/method with injected parameters (async)

        Args:
            services: ServiceProvider instance for DI
            event_loop: Event loop for running sync functions in executor
            *args: Positional arguments to pass to handler
            **kwargs: Keyword arguments to pass to handler (including url_segments)

        Returns:
            Coroutine or result depending on handler type
        """
        if self.is_class:
            raise TypeError(
                f"Cannot execute class {self.target}. Use create_instance() instead.")

        injected_kwargs = self.inject_parameters(services, **kwargs)

        if self.is_async:
            return self.target(*args, **injected_kwargs)
        else:
            # Sync handler - run in executor
            return event_loop.run_in_executor(
                None, lambda: self.target(*args, **injected_kwargs))

    def execute(self, services: 'ServiceProvider', *args: Any, **kwargs: Any) -> Any:
        """
        Execute handler with injected parameters (sync)

        Args:
            services: ServiceProvider instance for DI
            *args: Positional arguments to pass to handler
            **kwargs: Keyword arguments to pass to handler (including url_segments)

        Returns:
            Handler result

        Example:
            ```python
            def my_handler(logger: ILogger, name: str):
                logger.log(f"Hello {name}")
                return "done"

            plan = InjectionPlan(my_handler)
            result = plan.execute(services, name="Alice")
            ```
        """
        if self.is_class:
            raise TypeError(
                f"Cannot execute class {self.target}. Use create_instance() instead.")

        injected_kwargs = self.inject_parameters(services, **kwargs)
        # Merge with provided kwargs (provided ones take precedence)
        final_kwargs = {**injected_kwargs, **kwargs}

        return self.target(*args, **final_kwargs)

    def __repr__(self) -> str:
        target_name = self.target.__name__ if hasattr(
            self.target, '__name__') else str(self.target)
        target_type = "class" if self.is_class else "handler"
        return f"InjectionPlan({target_type}={target_name}, strategies={len(self.param_strategies)})"
