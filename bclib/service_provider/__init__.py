"""
Service Provider Module - Dependency Injection Container for BasisCore.Edge

A modular dependency injection system with support for:
- Multiple service lifetimes (Singleton, Scoped, Transient)
- Automatic constructor and method injection
- URL segment injection with type conversion
- Pre-compiled injection plans for high performance
- Async/sync handler support

Main Components:
- IServiceProvider: DI container interface
- ServiceProvider: Core DI container implementation
- ServiceLifetime: Enum for service scopes
- ServiceDescriptor: Service registration metadata
- InjectionPlan: Pre-compiled injection strategy (performance optimization)
- InjectionStrategy: Strategy pattern for parameter resolution

Example:
    ```python
    from bclib.utility import IServiceProvider, ServiceProvider, ServiceLifetime
    
    # Create and configure container
    services = ServiceProvider()
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_scoped(IDatabase, PostgresDatabase)
    services.add_transient(IEmailService, SmtpEmailService)
    
    # Use in handlers with automatic injection
    @app.restful_action()
    def handler(logger: ILogger, db: IDatabase, id: int):
        # logger, db auto-injected from DI
        # id auto-injected from URL segment with type conversion
        logger.log(f"Processing {id}")
        return db.get(id)
    ```
"""

# Performance optimization
from .injection_plan import InjectionPlan
from .injection_strategy import (InjectionStrategy, ServiceStrategy,
                                 ValueStrategy)
# Core DI container
from .iservice_provider import IServiceProvider
from .service_descriptor import ServiceDescriptor
# Service configuration
from .service_lifetime import ServiceLifetime
from .service_provider import ServiceProvider

__all__ = [
    # Main DI container
    'IServiceProvider',
    'ServiceProvider',

    # Configuration
    'ServiceLifetime',
    'ServiceDescriptor',

    # Performance optimization
    'InjectionPlan',

    # Strategy pattern (advanced usage)
    'InjectionStrategy',
    'ValueStrategy',
    'ServiceStrategy',
]
