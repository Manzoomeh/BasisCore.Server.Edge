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
from typing import (TYPE_CHECKING, Any, Callable, Coroutine, Dict, Type, Union,
                    get_args, get_origin, get_type_hints)

from .injection_strategy import (InjectionStrategy, ServiceStrategy,
                                 ValueStrategy)

if TYPE_CHECKING:
    from .service_provider import ServiceProvider


class InjectionPlan:
    """
    Pre-compiled injection plan for a handler or class

    Analyzes signature once at creation time and creates
    optimized injection strategies for each parameter.

    Can be used for:
    - Method/function calls with automatic DI
    - Class instantiation with constructor injection
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
        self._analyze()

    def _analyze(self) -> None:
        """Analyze target signature once and build injection strategies"""
        try:
            # Get the right callable to analyze
            if self.is_class:
                # For classes, analyze __init__
                callable_to_analyze = self.target.__init__
            else:
                # For functions/methods, analyze directly
                callable_to_analyze = self.target

            sig = inspect.signature(callable_to_analyze)
            type_hints = get_type_hints(callable_to_analyze)

            for param_name, param in sig.parameters.items():
                # Skip 'self' parameter for class constructors
                if param_name == 'self':
                    continue

                param_type = type_hints.get(param_name)

                if param_type is None:
                    continue

                # Check if it's a primitive type or Optional[primitive]
                actual_type = param_type
                is_optional = False

                # Handle Optional types (Union[X, None])
                if get_origin(param_type) is Union:
                    args = get_args(param_type)
                    # Check if it's Optional (Union with None)
                    if type(None) in args:
                        is_optional = True
                        # Get the non-None type
                        actual_type = next(
                            (arg for arg in args if arg is not type(None)), None)

                # Check if it's a primitive type that could be URL segment
                if actual_type in (str, int, float):
                    self.param_strategies[param_name] = ValueStrategy(
                        param_name, actual_type)
                else:
                    # Assume it's a service type
                    self.param_strategies[param_name] = ServiceStrategy(
                        param_type)

        except Exception:
            # If analysis fails, fall back to empty strategies
            pass

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
            except Exception:
                # Skip parameter if resolution fails
                continue

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
