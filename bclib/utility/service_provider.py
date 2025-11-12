"""
Service Provider - Dependency Injection Container for BasisCore.Edge

Provides dependency injection capabilities with support for different service lifetimes:
- Singleton: One instance for the entire application
- Scoped: One instance per request/scope
- Transient: New instance every time

Example:
    ```python
    # Register services
    services = ServiceProvider()
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_scoped(IDatabase, PostgresDatabase)
    services.add_transient(IEmailService, SmtpEmailService)
    
    # Resolve service
    logger = services.get_service(ILogger)
    logger.log("Application started")
    ```
"""
import inspect
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime/scope management"""
    SINGLETON = "singleton"    # One instance for entire application
    SCOPED = "scoped"         # One instance per request/scope
    TRANSIENT = "transient"   # New instance every time


class ServiceDescriptor:
    """
    Describes how a service should be created and managed

    A service can be registered in three ways:
    1. Implementation type: ServiceProvider will instantiate it
    2. Factory function: Custom creation logic
    3. Instance: Pre-created instance (singleton only)
    """

    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ):
        """
        Initialize service descriptor

        Args:
            service_type: The interface or abstract type to register
            implementation: Concrete implementation type (will be instantiated)
            factory: Factory function that returns an instance
            instance: Pre-created instance (for singletons)
            lifetime: Service lifetime (singleton/scoped/transient)
        """
        self.service_type = service_type
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime


class ServiceProvider:
    """
    Dependency Injection Container

    Manages service registration, resolution, and lifecycle.
    Supports three lifetimes: singleton, scoped, and transient.

    Example:
        ```python
        # Create container
        services = ServiceProvider()

        # Register services
        services.add_singleton(ILogger, ConsoleLogger)
        services.add_scoped(IDatabase, PostgresDatabase)
        services.add_transient(IEmailService, factory=lambda: SmtpEmailService("smtp.gmail.com"))

        # Resolve services
        logger = services.get_service(ILogger)
        db = services.get_service(IDatabase)

        # Create scope for request
        request_services = services.create_scope()
        request_db = request_services.get_service(IDatabase)  # New scoped instance
        request_services.clear_scope()  # Clean up after request
        ```
    """

    def __init__(self):
        """Initialize service provider with empty registrations"""
        self._descriptors: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}

    def add_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'ServiceProvider':
        """
        Register a singleton service (one instance for entire application)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function to create the service
            instance: Pre-created instance

        Returns:
            Self for chaining

        Example:
            ```python
            # Register by implementation type
            services.add_singleton(ILogger, ConsoleLogger)

            # Register by factory
            services.add_singleton(ILogger, factory=lambda: ConsoleLogger())

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
        self._descriptors[service_type] = descriptor

        # If instance provided, cache it immediately
        if instance is not None:
            self._singletons[service_type] = instance

        return self

    def add_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'ServiceProvider':
        """
        Register a scoped service (one instance per request/scope)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function to create the service

        Returns:
            Self for chaining

        Example:
            ```python
            # Register by implementation type
            services.add_scoped(IDatabase, PostgresDatabase)

            # Register by factory
            services.add_scoped(IDatabase, factory=lambda: PostgresDatabase("connection_string"))
            ```
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED
        )
        self._descriptors[service_type] = descriptor
        return self

    def add_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'ServiceProvider':
        """
        Register a transient service (new instance every time)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function to create the service

        Returns:
            Self for chaining

        Example:
            ```python
            # Register by implementation type
            services.add_transient(IEmailService, SmtpEmailService)

            # Register by factory
            services.add_transient(IEmailService, factory=lambda: SmtpEmailService("smtp.gmail.com"))
            ```
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        self._descriptors[service_type] = descriptor
        return self

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Resolve and return a service instance

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance or None if not registered

        Example:
            ```python
            logger = services.get_service(ILogger)
            if logger:
                logger.log("Service resolved")
            ```
        """
        if service_type not in self._descriptors:
            return None

        descriptor = self._descriptors[service_type]

        # Singleton: return cached or create once
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            instance = self._create_instance(descriptor)
            if instance is not None:
                self._singletons[service_type] = instance
            return instance

        # Scoped: return scoped or create for this scope
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]
            instance = self._create_instance(descriptor)
            if instance is not None:
                self._scoped_instances[service_type] = instance
            return instance

        # Transient: always create new
        else:
            return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """
        Create service instance based on descriptor

        Supports automatic constructor injection based on type hints.
        If constructor has typed parameters, they will be resolved from DI container.

        Args:
            descriptor: Service descriptor

        Returns:
            New service instance
        """
        # Direct instance (already created)
        if descriptor.instance is not None:
            return descriptor.instance

        # Factory function
        if descriptor.factory is not None:
            return descriptor.factory()

        # Implementation type with constructor injection
        if descriptor.implementation is not None:
            return self._create_with_constructor_injection(descriptor.implementation)

        # Use service type itself as implementation
        return self._create_with_constructor_injection(descriptor.service_type)

    def _create_with_constructor_injection(self, implementation_type: Type[T]) -> T:
        """
        Create instance with automatic constructor injection based on type hints

        Analyzes the __init__ method's type hints and automatically resolves
        dependencies from the DI container.

        Args:
            implementation_type: The class to instantiate

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
            # Get __init__ signature
            sig = inspect.signature(implementation_type.__init__)

            # Get type hints for constructor parameters
            try:
                type_hints = get_type_hints(implementation_type.__init__)
            except Exception:
                # If type hints fail, create without injection
                return implementation_type()

            # Build constructor arguments
            kwargs = {}

            for param_name, param in sig.parameters.items():
                # Skip 'self' parameter
                if param_name == 'self':
                    continue

                # Get type hint for this parameter
                param_type = type_hints.get(param_name)

                if param_type is not None:
                    # Try to resolve from DI container
                    service = self.get_service(param_type)

                    if service is not None:
                        kwargs[param_name] = service
                    elif param.default == inspect.Parameter.empty:
                        # Required parameter but not in DI container
                        # Try to create it if it's not registered
                        pass
                    else:
                        # Has default value, use it
                        pass

            # Create instance with injected dependencies
            return implementation_type(**kwargs)

        except Exception:
            # Fallback to parameterless constructor
            try:
                return implementation_type()
            except Exception:
                return None

    def inject_dependencies(self, handler: Callable, *args, **kwargs) -> dict:
        """
        Inject dependencies from DI container into handler parameters

        Analyzes the handler's signature and type hints to automatically
        resolve and inject services. Already-provided arguments are skipped.

        Args:
            handler: The handler function to inject dependencies into
            *args: Positional arguments already being passed
            **kwargs: Keyword arguments already being passed

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
        injected_kwargs = {}

        try:
            # Get handler signature and type hints
            sig = inspect.signature(handler)
            type_hints = get_type_hints(handler)

            # Inject dependencies for each parameter
            for param_name, param in sig.parameters.items():
                # Skip if already provided in kwargs
                if param_name in kwargs:
                    continue

                # Get type hint for this parameter
                param_type = type_hints.get(param_name)

                if param_type is None:
                    continue

                # Check if it's already in positional args by type
                if any(isinstance(arg, param_type) for arg in args):
                    continue

                # Try to resolve from DI container
                service = self.get_service(param_type)
                if service is not None:
                    injected_kwargs[param_name] = service

        except Exception:
            # If DI fails, continue without injection
            pass

        return injected_kwargs

    def create_scope(self) -> 'ServiceProvider':
        """
        Create a new scope for scoped services (per-request)

        Returns:
            New ServiceProvider with same registrations but fresh scoped instances

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
        scoped_provider._singletons = self._singletons
        # New scoped_instances for this scope
        return scoped_provider

    def clear_scope(self):
        """
        Clear scoped instances (call at end of request)

        Frees memory by removing scoped service instances.
        Singleton instances are preserved.
        """
        self._scoped_instances.clear()

    def invoke_method(self, method: Callable, *args, **kwargs) -> Any:
        """
        Invoke a method with automatic dependency injection for its parameters

        Type-hinted parameters are automatically resolved from the DI container.
        Explicitly provided args/kwargs take precedence over DI resolution.

        Args:
            method: The method/function to invoke
            *args: Positional arguments (override DI for positional params)
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Method return value

        Example:
            ```python
            def process_data(logger: ILogger, db: IDatabase, data: str):
                logger.log(f"Processing: {data}")
                return db.save(data)

            # Invoke with DI - logger and db injected automatically
            result = services.invoke_method(process_data, data="test")

            # Or as decorator
            @services.invoke_method
            async def handler(logger: ILogger, request_data: dict):
                logger.log("Handler called")
                return {"status": "ok"}
            ```
        """
        try:
            # Use inject_dependencies to get injected parameters
            injected_kwargs = self.inject_dependencies(method, *args, **kwargs)

            # Merge with provided kwargs
            final_kwargs = {**kwargs, **injected_kwargs}

            # Invoke method with injected dependencies
            return method(*args, **final_kwargs)

        except Exception as e:
            # Fallback to direct call
            return method(*args, **kwargs)

    async def invoke_method_async(self, method: Callable, *args, **kwargs) -> Any:
        """
        Invoke an async method with automatic dependency injection

        Type-hinted parameters are automatically resolved from the DI container.
        Explicitly provided args/kwargs take precedence over DI resolution.

        Args:
            method: The async method/function to invoke
            *args: Positional arguments (override DI for positional params)
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Awaited method return value

        Example:
            ```python
            async def process_async(logger: ILogger, db: IDatabase, data: str):
                logger.log(f"Processing: {data}")
                return await db.save_async(data)

            # Invoke async method with DI
            result = await services.invoke_method_async(process_async, data="test")
            ```
        """
        try:
            # Use inject_dependencies to get injected parameters
            injected_kwargs = self.inject_dependencies(method, *args, **kwargs)

            # Merge with provided kwargs
            final_kwargs = {**kwargs, **injected_kwargs}

            # Invoke async method with injected dependencies
            return await method(*args, **final_kwargs)

        except Exception as e:
            # Fallback to direct call
            return await method(*args, **kwargs)

    def invoke(self, method: Callable, *args, **kwargs):
        """
        Smart invoke - automatically detects if method is async or sync and calls appropriately

        This is the recommended method to use as it handles both sync and async functions
        automatically without needing to know which type the function is.

        Args:
            method: The method/function to invoke (sync or async)
            *args: Positional arguments (override DI for positional params)
            **kwargs: Keyword arguments (override DI for named params)

        Returns:
            Method return value (or coroutine for async methods)

        Example:
            ```python
            # Works with sync functions
            def sync_func(logger: ILogger, data: str):
                logger.log(data)
                return "done"

            result = services.invoke(sync_func, data="test")

            # Works with async functions
            async def async_func(logger: ILogger, db: IDatabase):
                await db.save()
                return "saved"

            result = await services.invoke(async_func)

            # In handlers - works for both
            result = await services.invoke(some_function, param="value")
            ```
        """
        # Check if method is a coroutine function (async)
        if inspect.iscoroutinefunction(method):
            return self.invoke_method_async(method, *args, **kwargs)
        else:
            return self.invoke_method(method, *args, **kwargs)

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

    def __repr__(self) -> str:
        """String representation of service provider"""
        return (
            f"ServiceProvider("
            f"registered={len(self._descriptors)}, "
            f"singletons={len(self._singletons)}, "
            f"scoped={len(self._scoped_instances)})"
        )
