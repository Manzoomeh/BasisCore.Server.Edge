"""
Service Provider - Main Dependency Injection Container

The core DI container that manages service registration, resolution, 
and lifecycle. Supports three lifetimes: singleton, scoped, and transient.

Features:
- Constructor injection based on type hints
- Method injection for handlers
- Automatic URL segment injection
- Async/sync handler support
- Scoped services for request isolation
"""
import inspect
import re
from typing import (Any, Callable, Dict, ForwardRef, Optional, Type, TypeVar,
                    get_type_hints)

from .ihosted_service import IHostedService
from .injection_plan import InjectionPlan
from .iservice_provider import IServiceProvider
from .service_descriptor import ServiceDescriptor
from .service_lifetime import ServiceLifetime

T = TypeVar('T')

# Pre-compiled regex for parsing generic string annotations (performance optimization)
_GENERIC_ANNOTATION_PATTERN = re.compile(
    r"^(\w+)\[(?:ForwardRef\()?['\"]([^'\"]+)['\"](?:\))?\]$"
)


class ServiceProvider(IServiceProvider):
    """
    Dependency Injection Container

    Manages service registration, resolution, and lifecycle.
    Supports three lifetimes: singleton, scoped, and transient.
    Also supports hosted services that are automatically instantiated at startup.

    NEW: Multiple Implementations per Interface
    -------------------------------------------
    Now supports registering multiple implementations for a single interface.
    Use get_service(Type) to get the first implementation, or get_service(list[Type])
    to get all implementations.

    Features:
        - Constructor injection based on type hints
        - Method injection for handlers
        - Multiple implementations per interface
        - Automatic list injection for multiple services
        - Three lifetimes: singleton, scoped, transient
        - Hosted services with initialization priority
        - Generic type support (e.g., ILogger['App'])

    Example:
        ```python
        # Create container
        services = ServiceProvider()

        # Register single implementation
        services.add_singleton(ILogger, ConsoleLogger)
        services.add_scoped(IDatabase, PostgresDatabase)

        # Register multiple implementations for same interface
        services.add_singleton(IListener, HttpListener)
        services.add_singleton(IListener, TcpListener)
        services.add_singleton(IListener, RabbitListener)

        # Resolve first implementation
        logger = services.get_service(ILogger)
        first_listener = services.get_service(IListener)  # Returns HttpListener

        # Resolve all implementations as list
        all_listeners = services.get_service(list[IListener])  # Returns [HttpListener, TcpListener, RabbitListener]

        # Automatic injection of multiple services
        class ListenerFactory:
            def __init__(self, listeners: list[IListener]):  # Auto-injected!
                self.listeners = listeners

        services.add_singleton(ListenerFactory)
        factory = services.get_service(ListenerFactory)  # Receives all listeners

        # Create scope for request
        request_services = services.create_scope()
        request_db = request_services.get_service(IDatabase)  # New scoped instance
        request_services.clear_scope()  # Clean up after request
        ```
    """

    def __init__(self) -> None:
        """Initialize service provider with empty registrations"""
        # Changed: Now stores list of descriptors per service type to support multiple implementations
        self._descriptors: Dict[Type, list[ServiceDescriptor]] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        # Cache for generic singleton instances: (base_type, generic_args_tuple) -> instance
        self._generic_singleton_instances: Dict[tuple, Any] = {}
        # Cache for multiple instances: service_type -> list[instances]
        self._scoped_instances_list: Dict[Type, list[Any]] = {}
        self._generic_singleton_instances_list: Dict[tuple, list[Any]] = {}

    def add_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider', Any], T]] = None,
        instance: Optional[T] = None
    ) -> 'IServiceProvider':
        """
        Register a singleton service (one instance for entire application)

        Supports multiple implementations: calling this multiple times with the same
        service_type will register additional implementations. Use get_service(Type)
        to get the first one, or get_service(list[Type]) to get all.

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider and **kwargs, creates the service
            instance: Pre-created instance

        Returns:
            Self for chaining

        Example:
            ```python
            # Register by implementation type
            services.add_singleton(ILogger, ConsoleLogger)

            # Register multiple implementations for same interface
            services.add_singleton(IListener, HttpListener)
            services.add_singleton(IListener, TcpListener)
            services.add_singleton(IListener, RabbitListener)

            # Register by factory (with ServiceProvider and **kwargs access)
            services.add_singleton(ILogger, factory=lambda sp, **kwargs: ConsoleLogger())
            services.add_singleton(IDatabase, factory=lambda sp, **kwargs: PostgresDB(sp.get_service(ILogger)))

            # Factory can use generic_type_args from kwargs
            services.add_singleton(ILogger, factory=lambda sp, **kwargs: ConsoleLogger.create_logger(
                kwargs.get('generic_type_args', ('App',))[0], options
            ))

            # Register existing instance
            logger = ConsoleLogger()
            services.add_singleton(ILogger, instance=logger)
            ```
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        # Support multiple implementations: append to list instead of replacing
        if service_type not in self._descriptors:
            self._descriptors[service_type] = []
        self._descriptors[service_type].append(descriptor)
        return self

    def add_hosted(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider', Any], T]] = None,
        priority: int = 0
    ) -> 'IServiceProvider':
        """
        Register a hosted service (singleton instantiated at application startup)

        Hosted services are like singletons but are automatically instantiated
        when initialize_hosted_services_async() is called (typically at listener startup).
        Useful for background services, initializers, and startup tasks.

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider and **kwargs, creates the service
            priority: Initialization priority (higher = initialized first, default=0)

        Returns:
            Self for chaining

        Example:
            ```python
            # Register background service
            services.add_hosted(IBackgroundService, BackgroundWorker)

            # Register with priority (database initialized before background worker)
            services.add_hosted(IDatabase, DatabaseService, priority=100)
            services.add_hosted(IBackgroundWorker, BackgroundWorker, priority=50)

            # Register with factory (receives ServiceProvider and **kwargs)
            services.add_hosted(IStartupTask, factory=lambda sp, **kwargs: StartupTask(sp.get_service(ILogger)))

            # Initialize all hosted services at startup (sorted by priority)
            await services.initialize_hosted_services_async()
            ```
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
            is_hosted=True,
            priority=priority
        )
        # Support multiple implementations: append to list instead of replacing
        if service_type not in self._descriptors:
            self._descriptors[service_type] = []
        self._descriptors[service_type].append(descriptor)
        return self

    def add_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider', Any], T]] = None
    ) -> 'IServiceProvider':
        """
        Register a scoped service (one instance per scope/request)

        Supports multiple implementations: calling this multiple times with the same
        service_type will register additional implementations.

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider and **kwargs, creates the service

        Returns:
            Self for chaining

        Example:
            ```python
            # Register by implementation type
            services.add_scoped(IDatabase, PostgresDatabase)

            # Register multiple implementations
            services.add_scoped(IMiddleware, AuthMiddleware)
            services.add_scoped(IMiddleware, LoggingMiddleware)

            # Register by factory (receives ServiceProvider and **kwargs)
            services.add_scoped(IDatabase, factory=lambda sp, **kwargs: PostgresDatabase("connection_string"))
            services.add_scoped(ICache, factory=lambda sp, **kwargs: RedisCache(sp.get_service(ILogger)))
            ```
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED
        )
        # Support multiple implementations: append to list instead of replacing
        if service_type not in self._descriptors:
            self._descriptors[service_type] = []
        self._descriptors[service_type].append(descriptor)
        return self

    def add_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[['IServiceProvider', Any], T]] = None
    ) -> 'IServiceProvider':
        """
        Register a transient service (new instance every time)

        Supports multiple implementations: calling this multiple times with the same
        service_type will register additional implementations. Each resolution creates
        new instances.

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider and **kwargs, creates the service

        Returns:
            Self for chaining

        Example:
            ```python
            # Register by implementation type
            services.add_transient(IEmailService, SmtpEmailService)

            # Register multiple implementations (each call creates new instances)
            services.add_transient(INotification, EmailNotification)
            services.add_transient(INotification, SmsNotification)
            services.add_transient(INotification, PushNotification)

            # Register by factory (receives ServiceProvider and **kwargs)
            services.add_transient(IEmailService, factory=lambda sp, **kwargs: SmtpEmailService("smtp.gmail.com"))
            services.add_transient(INotifier, factory=lambda sp, **kwargs: Notifier(sp.get_service(ILogger), sp.get_service(IEmailService)))
            ```
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        # Support multiple implementations: append to list instead of replacing
        if service_type not in self._descriptors:
            self._descriptors[service_type] = []
        self._descriptors[service_type].append(descriptor)
        return self

    def get_service(self, service_type: Type[T], **kwargs: Any) -> Optional[T]:
        """
        Resolve and return a service instance

        Supports both single and multiple implementations:
        - For Type[T]: Returns first registered implementation
        - For list[Type[T]]: Returns all registered implementations as list

        Args:
            service_type: The service type to resolve (can be list[Type] for multiple)
            **kwargs: Additional parameters for constructor injection

        Returns:
            Service instance(s) or None if not registered

        Example:
            ```python
            # Get first logger
            logger = services.get_service(ILogger)

            # Get all loggers
            all_loggers = services.get_service(list[ILogger])

            # Register multiple implementations
            services.add_singleton(IListener, HttpListener)
            services.add_singleton(IListener, TcpListener)
            services.add_singleton(IListener, RabbitListener)

            # Get first listener
            listener = services.get_service(IListener)  # Returns HttpListener

            # Get all listeners
            listeners = services.get_service(list[IListener])  # Returns [HttpListener, TcpListener, RabbitListener]
            ```
        """
        from typing import get_args, get_origin

        # Check if requesting list of services
        origin = get_origin(service_type)
        if origin is list:
            # Requesting list[SomeType] - return all implementations
            type_args = get_args(service_type)
            if type_args:
                inner_type = type_args[0]
                return self._get_all_services(inner_type, **kwargs)
            return None

        # Single service request - return first implementation
        return self._get_single_service(service_type, **kwargs)

    def _get_all_services(self, service_type: Type[T], **kwargs: Any) -> list[T]:
        """
        Get all registered implementations for a service type

        This method resolves all implementations registered for a given service type.
        Each implementation respects its lifetime:
        - Singleton: Returns same instance across calls
        - Scoped: Returns same instance within scope
        - Transient: Creates new instance each time

        Args:
            service_type: The service type to resolve
            **kwargs: Additional parameters for constructor injection

        Returns:
            List of all service instances (empty list if not registered)

        Example:
            ```python
            # Register multiple implementations
            services.add_singleton(IListener, HttpListener)
            services.add_singleton(IListener, TcpListener)
            services.add_transient(IListener, RabbitListener)

            # Get all - HttpListener and TcpListener are singletons, RabbitListener is new each time
            listeners_1 = services._get_all_services(IListener)
            listeners_2 = services._get_all_services(IListener)

            # listeners_1[0] is listeners_2[0]  # True (singleton)
            # listeners_1[1] is listeners_2[1]  # True (singleton)
            # listeners_1[2] is listeners_2[2]  # False (transient)
            ```
        """
        from typing import get_args, get_origin

        # Find descriptors for this type
        descriptors = None
        base_type_for_cache = None

        if service_type in self._descriptors:
            descriptors = self._descriptors[service_type]
            base_type_for_cache = service_type
        else:
            # Try base type for generics
            origin = get_origin(service_type)
            if origin is not None and origin in self._descriptors:
                descriptors = self._descriptors[origin]
                base_type_for_cache = origin
                type_args = get_args(service_type)
                if type_args:
                    kwargs = {**kwargs, 'generic_type_args': type_args}

        if not descriptors:
            return []

        # Create instances for all descriptors
        instances = []
        for descriptor in descriptors:
            instance = self._resolve_descriptor(
                descriptor, base_type_for_cache, service_type, **kwargs)
            if instance is not None:
                instances.append(instance)

        return instances

    def _get_single_service(self, service_type: Type[T], **kwargs: Any) -> Optional[T]:
        """
        Get first registered implementation for a service type

        When multiple implementations are registered for the same interface,
        this method returns the first one (registered first). This provides
        backward compatibility while supporting the multiple implementations feature.

        Args:
            service_type: The service type to resolve
            **kwargs: Additional parameters for constructor injection

        Returns:
            First service instance or None if not registered

        Example:
            ```python
            # Register multiple implementations
            services.add_singleton(IListener, HttpListener)   # First
            services.add_singleton(IListener, TcpListener)    # Second
            services.add_singleton(IListener, RabbitListener) # Third

            # Get first implementation
            listener = services.get_service(IListener)  # Returns HttpListener
            ```
        """
        # Handle string annotations (from __future__ annotations)
        # These can be simple ("MyClass") or complex ("IOptions['database']")
        if isinstance(service_type, str):
            # Try to parse generic type from string annotation using pre-compiled pattern
            generic_match = _GENERIC_ANNOTATION_PATTERN.match(service_type)

            if generic_match:
                # Extract base type name and generic argument
                base_type_name = generic_match.group(1)
                generic_arg = generic_match.group(2)

                # Try to find base type in registered descriptors
                # Look for type with matching __name__
                for registered_type in self._descriptors:
                    if hasattr(registered_type, '__name__') and registered_type.__name__ == base_type_name:
                        # Found the base type, pass generic arg via kwargs
                        descriptors = self._descriptors[registered_type]
                        base_type_for_cache = registered_type
                        kwargs = {
                            **kwargs, 'generic_type_args': (ForwardRef(generic_arg),)}
                        break
                else:
                    # Base type not found
                    return None
            else:
                # Simple string annotation - not supported yet
                return None
        else:
            # Try exact match first
            if service_type in self._descriptors:
                descriptors = self._descriptors[service_type]
                base_type_for_cache = service_type
            else:
                # If not found and it's a generic type, try base type
                from typing import get_args, get_origin
                origin = get_origin(service_type)
                if origin is not None and origin in self._descriptors:
                    # Found base generic type (e.g., ILogger when requesting ILogger['App'])
                    descriptors = self._descriptors[origin]
                    base_type_for_cache = origin
                    # Pass generic type arguments via kwargs
                    type_args = get_args(service_type)
                    if type_args:
                        kwargs = {**kwargs, 'generic_type_args': type_args}
                else:
                    # Not found at all
                    return None

        # Get first descriptor (for backward compatibility)
        if not descriptors:
            return None
        descriptor = descriptors[0]

        return self._resolve_descriptor(descriptor, base_type_for_cache, service_type, **kwargs)

    def _resolve_descriptor(self, descriptor: ServiceDescriptor, base_type_for_cache: Type, service_type: Type, **kwargs: Any) -> Optional[Any]:
        """
        Resolve a single descriptor to an instance

        Handles caching for singleton/scoped lifetimes.

        Args:
            descriptor: Service descriptor to resolve
            base_type_for_cache: Base type for cache key
            service_type: Original requested service type
            **kwargs: Additional parameters for constructor injection

        Returns:
            Service instance or None
        """
        # Singleton: return cached or create once
        # For generic types, cache per (base_type, generic_args) combination
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            # Check if this is a generic singleton with type arguments
            generic_type_args = kwargs.get('generic_type_args')

            if generic_type_args:
                # Create cache key and check generic singleton cache
                cache_key = self._make_generic_cache_key(
                    base_type_for_cache, generic_type_args)

                if cache_key in self._generic_singleton_instances:
                    return self._generic_singleton_instances[cache_key]

                # Create new instance and cache it
                instance = self._create_instance(descriptor, **kwargs)
                if instance is not None:
                    self._generic_singleton_instances[cache_key] = instance
                return instance
            else:
                # Non-generic singleton - use descriptor's instance cache
                if descriptor.instance is not None:
                    return descriptor.instance
                instance = self._create_instance(descriptor, **kwargs)
                if instance is not None:
                    descriptor.instance = instance
                return instance

        # Scoped: return scoped or create for this scope
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            # Check if this is a generic scoped service with type arguments
            generic_type_args = kwargs.get('generic_type_args')

            if generic_type_args:
                # Create cache key and check scoped cache
                cache_key = self._make_generic_cache_key(
                    base_type_for_cache, generic_type_args)

                if cache_key in self._scoped_instances:
                    return self._scoped_instances[cache_key]

                # Create new instance and cache it
                instance = self._create_instance(descriptor, **kwargs)
                if instance is not None:
                    self._scoped_instances[cache_key] = instance
                return instance
            else:
                # Non-generic scoped service
                if service_type in self._scoped_instances:
                    return self._scoped_instances[service_type]
                instance = self._create_instance(descriptor, **kwargs)
                if instance is not None:
                    self._scoped_instances[service_type] = instance
                return instance

        # Transient: always create new
        else:
            return self._create_instance(descriptor, **kwargs)

    @staticmethod
    def _make_generic_cache_key(base_type: Type, generic_args: tuple) -> tuple:
        """
        Create hashable cache key for generic service instances

        Converts generic type arguments to strings for use as dictionary keys.
        ForwardRef objects are converted to their forward argument string.

        Args:
            base_type: The base service type (e.g., IOptions)
            generic_args: Tuple of generic type arguments (e.g., (ForwardRef('database'),))

        Returns:
            Tuple of (base_type, tuple of string arguments) suitable for dict key

        Example:
            >>> _make_generic_cache_key(IOptions, (ForwardRef('database'),))
            (IOptions, ('database',))
        """
        cache_key_args = tuple(
            arg.__forward_arg__ if isinstance(arg, ForwardRef) else str(arg)
            for arg in generic_args
        )
        return (base_type, cache_key_args)

    def _create_instance(self, descriptor: ServiceDescriptor, **kwargs: Any) -> Any:
        """
        Create service instance based on descriptor

        Supports automatic constructor injection based on type hints.
        If constructor has typed parameters, they will be resolved from DI container.

        Args:
            descriptor: Service descriptor
            **kwargs: Additional parameters for constructor injection

        Returns:
            New service instance
        """
        # Direct instance (already created)
        if descriptor.instance is not None:
            return descriptor.instance

        # Factory function (pass ServiceProvider and **kwargs for dependency resolution)
        if descriptor.factory is not None:
            return descriptor.factory(self, **kwargs)

        # Implementation type with constructor injection
        if descriptor.implementation is not None:
            return self._create_with_constructor_injection(descriptor.implementation, **kwargs)

        # Use service type itself as implementation
        return self._create_with_constructor_injection(descriptor.service_type, **kwargs)

    def _create_with_constructor_injection(self, implementation_type: Type[T], **kwargs: Any) -> Optional[T]:
        """
        Create instance with automatic constructor injection based on type hints

        Uses InjectionPlan for optimized parameter resolution.
        Analyzes the __init__ method's type hints and automatically resolves
        dependencies from the DI container.

        Args:
            implementation_type: The class to instantiate
            **kwargs: Additional parameters for constructor injection

        Returns:
            Instance with injected dependencies

        Example:
            ```python
            class MyService:
                def __init__(self, logger: ILogger, db: IDatabase):
                    self.logger = logger
                    self.db = db

            # Automatically injects logger and db from container
            services.add_transient(MyService)
            instance = services.get_service(MyService)
            ```
        """
        try:
            # Use InjectionPlan for optimized injection
            plan = InjectionPlan(implementation_type)
            return plan.create_instance(self, **kwargs)
        except TypeError as e:
            # If it's a TypeError about missing arguments, the class might not support DI
            # Try parameterless constructor as fallback
            if "missing" in str(e) and "required positional argument" in str(e):
                try:
                    return implementation_type()
                except TypeError:
                    # Parameterless constructor also failed, re-raise original error
                    raise e
            else:
                # Other TypeError, re-raise
                raise
        except Exception:
            # For other exceptions during injection, try parameterless constructor
            try:
                return implementation_type()
            except:
                # If both fail, re-raise original exception
                raise

    def inject_dependencies(self, handler: Callable, **kwargs: Any) -> Dict[str, Any]:
        """
        Inject dependencies from DI container into handler parameters

        Uses InjectionPlan for optimized parameter resolution.
        Analyzes the handler's signature and type hints to automatically
        resolve and inject services. Also injects values from kwargs.

        Args:
            handler: The handler function to inject dependencies into
            **kwargs: Keyword arguments already being passed (including url_segments)

        Returns:
            Dictionary of parameter names and resolved service instances

        Example:
            ```python
            def process_order(logger: ILogger, db: IDatabase, order_id: str):
                logger.log(f"Processing order {order_id}")
                db.save(order_id)

            # Inject logger and db, but not order_id (already provided)
            injected = services.inject_dependencies(process_order, order_id="123")
            # injected = {"logger": <ConsoleLogger>, "db": <PostgresDatabase>}

            # Call with injected dependencies
            process_order(order_id="123", **injected)
            ```
        """
        try:
            # Use InjectionPlan for optimized injection
            plan = InjectionPlan(handler)
            injected_kwargs = plan.inject_parameters(self, **kwargs)

            # Filter out already provided kwargs
            return {k: v for k, v in injected_kwargs.items() if k not in kwargs}

        except Exception:
            # If DI fails, continue without injection
            return {}

    def create_scope(self) -> 'IServiceProvider':
        """
        Create a new scope for scoped services (per-request)

        Returns:
            New IServiceProvider with same registrations but fresh scoped instances

        Example:
            ```python
            # Create scope for each request
            request_services = app.services.create_scope()

            # Use scoped services
            db = request_services.get_service(IDatabase)

            # Clean up after request
            request_services.clear_scope()
            ```
        """
        scoped_provider = ServiceProvider()
        scoped_provider._descriptors = self._descriptors
        # New scoped_instances for this scope
        return scoped_provider

    def clear_scope(self) -> None:
        """
        Clear scoped instances (call at end of request)

        Frees memory by removing scoped service instances.
        Singleton instances are preserved.
        """
        self._scoped_instances.clear()

    def invoke_method(self, method: Callable, **kwargs: Any) -> Any:
        """
        Invoke a method with automatic dependency injection for its parameters

        Uses InjectionPlan for optimized parameter resolution.
        Type-hinted parameters are automatically resolved from the DI container.
        Explicitly provided kwargs take precedence over DI resolution.

        Args:
            method: The method/function to invoke
            **kwargs: Keyword arguments (override DI for named params, including url_segments)

        Returns:
            Method return value

        Example:
            ```python
            def process_data(logger: ILogger, db: IDatabase, data: str):
                logger.log(f"Processing: {data}")
                return db.save(data)

            # Invoke with DI - logger and db injected automatically
            result = services.invoke_method(process_data, data="test")
            ```
        """
        try:
            # Use inject_dependencies to get injected parameters
            injected_kwargs = self.inject_dependencies(method, **kwargs)

            # Merge with provided kwargs
            final_kwargs = {**kwargs, **injected_kwargs}

            # Invoke method with injected dependencies
            return method(**final_kwargs)

        except Exception:
            # Fallback to direct call
            return method(**kwargs)

    async def invoke_method_async(self, method: Callable, event_loop: Any, **kwargs: Any) -> Any:
        """
        Invoke an async method with automatic dependency injection

        Uses InjectionPlan for optimized parameter resolution.
        Type-hinted parameters are automatically resolved from the DI container.
        Explicitly provided kwargs take precedence over DI resolution.

        Args:
            method: The async method/function to invoke
            event_loop: Event loop for running sync functions in executor
            **kwargs: Keyword arguments (override DI for named params, including url_segments)

        Returns:
            Awaited method return value

        Example:
            ```python
            async def process_async(logger: ILogger, db: IDatabase, data: str):
                logger.log(f"Processing: {data}")
                return await db.save_async(data)

            # Invoke async method with DI
            result = await services.invoke_method_async(process_async, event_loop, data="test")
            ```
        """
        try:
            # Use InjectionPlan for optimized injection
            plan = InjectionPlan(method)
            result = plan.execute_async(self, event_loop, **kwargs)

            # If result is coroutine, await it
            if inspect.iscoroutine(result):
                return await result
            return result

        except Exception:
            # Fallback to direct call
            return await method(**kwargs)

    def invoke(self, method: Callable, event_loop: Any, **kwargs: Any) -> Any:
        """
        Smart invoke - automatically detects if method is async or sync and calls appropriately

        Uses InjectionPlan for optimized parameter resolution.
        This is the recommended method to use as it handles both sync and async functions
        automatically without needing to know which type the function is.

        Args:
            method: The method/function to invoke (sync or async)
            event_loop: Event loop for running async/sync methods
            **kwargs: Keyword arguments (override DI for named params, including url_segments)

        Returns:
            Method return value (or coroutine for async methods)

        Example:
            ```python
            # Works with sync functions
            def sync_func(logger: ILogger, data: str):
                logger.log(data)
                return "done"

            result = services.invoke(sync_func, event_loop, data="test")

            # Works with async functions
            async def async_func(logger: ILogger, db: IDatabase):
                await db.save()
                return "saved"

            result = await services.invoke(async_func, event_loop)

            # In handlers - works for both
            result = await services.invoke(some_function, event_loop, param="value")
            ```
        """
        # Check if method is a coroutine function (async)
        if inspect.iscoroutinefunction(method):
            return self.invoke_method_async(method, event_loop, **kwargs)
        else:
            return self.invoke_method(method, **kwargs)

    def create_instance(self, class_type: Type[T], **kwargs: Any) -> T:
        """
        Create an instance of a class with automatic dependency injection

        Uses InjectionPlan for optimized parameter resolution.
        Type-hinted constructor parameters are automatically resolved from the DI container.
        Explicitly provided kwargs take precedence over DI resolution.

        Args:
            class_type: The class to instantiate
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Instance with injected dependencies

        Example:
            ```python
            class MyService:
                def __init__(self, logger: ILogger, db: IDatabase, config: str):
                    self.logger = logger
                    self.db = db
                    self.config = config

            # Create instance with DI - logger and db injected automatically
            instance = services.create_instance(MyService, config="production")

            # Without registration needed
            class AnotherService:
                def __init__(self, logger: ILogger):
                    self.logger = logger

            service = services.create_instance(AnotherService)
            ```
        """
        try:
            # Use InjectionPlan for optimized injection
            plan = InjectionPlan(class_type)
            return plan.create_instance(self, **kwargs)
        except Exception as ex:
            # Fallback to direct instantiation
            from bclib.logger.ilogger import ILogger
            logger = self.get_service(ILogger['ServiceProvider'])
            if logger:
                logger.error(
                    "ServiceProvider.create_instance: Failed to create instance of %s: %s",
                    class_type.__name__,
                    str(ex),
                    exc_info=True
                )
            return class_type(**kwargs)

    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered

        Args:
            service_type: The service type to check

        Returns:
            True if registered, False otherwise
        """
        return service_type in self._descriptors

    def get_lifetime(self, service_type: Type) -> Optional[ServiceLifetime]:
        """
        Get the lifetime of a registered service

        Args:
            service_type: The service type

        Returns:
            ServiceLifetime or None if not registered
        """
        descriptor = self._descriptors.get(service_type)
        return descriptor.lifetime if descriptor else None

    def remove_service(self, service_type: Type[T]) -> bool:
        """
        Remove a registered service from the container

        Removes the service descriptor and any cached instances (singleton or scoped).
        This is useful for testing, dynamic service replacement, or cleanup.

        Args:
            service_type: The service type to remove

        Returns:
            True if service was removed, False if it wasn't registered

        Example:
            ```python
            # Remove and replace a service
            services.remove_service(ILogger)
            services.add_singleton(ILogger, factory=lambda sp, **kw: NewLogger())

            # Clean up test registrations
            services.remove_service(IMockDatabase)
            ```
        """
        if service_type not in self._descriptors:
            return False

        # Remove descriptor
        del self._descriptors[service_type]

        # Remove scoped instance if exists
        if service_type in self._scoped_instances:
            del self._scoped_instances[service_type]

        return True

    async def invoke_in_executor(self, method: Callable, event_loop: Any, **kwargs: Any) -> Any:
        """
        Invoke a method with DI, running sync methods in thread pool to avoid blocking

        Uses InjectionPlan for optimized parameter resolution.
        This method is designed for HTTP servers where sync handlers should not block
        the event loop. Async handlers are awaited directly, sync handlers run in executor.

        Args:
            method: The method/function to invoke (sync or async)
            event_loop: The asyncio event loop for run_in_executor
            **kwargs: Keyword arguments (override DI for named params, including url_segments)

        Returns:
            Awaited method return value

        Example:
            ```python
            # In HTTP handler decorator
            @wraps(handler)
            async def wrapper(context):
                # Flatten url_segments into kwargs
                url_kwargs = context.url_segments.__dict__ if context.url_segments else {}
                return await context.services.invoke_in_executor(
                    handler, context.dispatcher.event_loop, **url_kwargs)
            ```
        """
        try:
            # Use InjectionPlan for optimized injection
            plan = InjectionPlan(method)
            result = plan.execute_async(self, event_loop, **kwargs)

            # If result is coroutine, await it
            if inspect.iscoroutine(result):
                return await result
            return result

        except Exception:
            # Fallback
            if inspect.iscoroutinefunction(method):
                return await method(**kwargs)
            else:
                return await event_loop.run_in_executor(
                    None, lambda: method(**kwargs))

    async def initialize_hosted_services_async(self) -> None:
        """
        Initialize all hosted services by instantiating them and calling start_async

        This should be called at application startup (typically in dispatcher.initialize_task_async)
        to instantiate all services registered with add_hosted and call their start_async method
        if they implement IHostedService.

        Services are initialized in two phases:
        1. Priority > 0: Sorted by priority (higher first)
        2. Priority = 0: Sorted by registration order

        Example:
            ```python
            # In dispatcher's initialize_task_async
            async def initialize_task_async(self):
                await self._service_provider.initialize_hosted_services_async()
                # ... rest of initialization
            ```
        """
        # Get all hosted descriptors from all service types (now lists)
        hosted_descriptors = []
        for descriptor_list in self._descriptors.values():
            for descriptor in descriptor_list:
                if descriptor.is_hosted and descriptor.instance is None:
                    hosted_descriptors.append(descriptor)

        # Separate into priority and non-priority services
        priority_services = [d for d in hosted_descriptors if d.priority > 0]
        default_services = [d for d in hosted_descriptors if d.priority == 0]

        # Sort priority services by priority (higher first)
        priority_services.sort(key=lambda d: d.priority, reverse=True)

        # Combine: priority services first, then default services in registration order
        sorted_descriptors = priority_services + default_services

        for descriptor in sorted_descriptors:
            # Instantiate the hosted service
            instance = self.get_service(descriptor.service_type)

            # Call start_async if service implements IHostedService
            if isinstance(instance, IHostedService):
                await instance.start_async()

    async def stop_hosted_services_async(self) -> None:
        """
        Stop all hosted services by calling stop_async for graceful shutdown

        This should be called during application shutdown (in dispatcher.listening's after_end)
        to call stop_async on all hosted services that implement IHostedService.

        Example:
            ```python
            # In dispatcher's listening method
            async def shutdown():
                await self._service_provider.stop_hosted_services_async()

            dispatcher.listening(after_end=shutdown())
            ```
        """
        # Iterate over all descriptor lists and their individual descriptors
        for descriptor_list in self._descriptors.values():
            for descriptor in descriptor_list:
                if descriptor.is_hosted and descriptor.instance is not None:
                    instance = descriptor.instance

                    # Call stop_async if service implements IHostedService
                    if isinstance(instance, IHostedService):
                        await instance.stop_async()

    def __repr__(self) -> str:
        """String representation of service provider"""
        singleton_count = sum(1 for d in self._descriptors.values()
                              if d.lifetime == ServiceLifetime.SINGLETON and d.instance is not None)
        return (
            f"ServiceProvider("
            f"registered={len(self._descriptors)}, "
            f"singletons={singleton_count}, "
            f"scoped={len(self._scoped_instances)})"
        )
