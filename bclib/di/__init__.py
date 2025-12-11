"""
Service Provider Module - Dependency Injection Container for BasisCore.Edge

A modular dependency injection system with support for:
- Multiple service lifetimes (Singleton, Scoped, Transient)
- Automatic constructor and method injection
- URL segment injection with type conversion
- Pre-compiled injection plans for high performance
- Async/sync handler support

Main Components:
- IServiceContainer: Container registration and management interface
- IServiceProvider: Service resolution and DI interface (extends IServiceContainer)
- ServiceProvider: Core DI container implementation
- ServiceLifetime: Enum for service scopes
- ServiceDescriptor: Service registration metadata
- InjectionPlan: Pre-compiled injection strategy (performance optimization)
- InjectionStrategy: Strategy pattern for parameter resolution

Example:
    ```python
    from bclib.di import IServiceProvider, ServiceProvider, ServiceLifetime
    
    # Create and configure container
    services = ServiceProvider()
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_scoped(IDatabase, PostgresDatabase)
    services.add_transient(IEmailService, SmtpEmailService)
    
    # Use in handlers with automatic injection
    @app.restful_handler()
    def handler(logger: ILogger, db: IDatabase, id: int):
        # logger, db auto-injected from DI
        # id auto-injected from URL segment with type conversion
        logger.log(f"Processing {id}")
        return db.get(id)
    ```
"""

# Hosted service interface
import asyncio
import sys
from typing import Optional

from .ihosted_service import IHostedService
# Performance optimization
from .injection_plan import InjectionPlan
from .injection_strategy import (InjectionStrategy, ServiceStrategy,
                                 ValueStrategy)
# Core DI container
from .iservice_container import IServiceContainer
from .iservice_provider import IServiceProvider
from .service_descriptor import ServiceDescriptor
# Service configuration
from .service_lifetime import ServiceLifetime

__all__ = [
    # Main DI container
    'IServiceContainer',
    'IServiceProvider',
    'ServiceProvider',

    # Configuration
    'ServiceLifetime',
    'ServiceDescriptor',

    # Hosted services
    'IHostedService',

    # Performance optimization
    'InjectionPlan',

    # Strategy pattern (advanced usage)
    'InjectionStrategy',
    'ValueStrategy',
    'ServiceStrategy',
]


def create_service_provider(loop: Optional[asyncio.AbstractEventLoop] = None) -> IServiceContainer:
    """
    Create and configure the main ServiceProvider (DI Container)

    This function initializes the ServiceProvider with default services
    required for BasisCore.Edge applications, including logging, database
    management, listener factories, and dispatcher services.

    Args:
        options (AppOptions): Application configuration options
        loop (Optional[asyncio.AbstractEventLoop]): Optional event loop to use

    Returns:
        IDispatcher: Configured dispatcher instance for routing requests

    Example:
        ```python
        from bclib import edge
        from bclib.di import create_service_provider

        # Load app options (e.g., from config file)
        app_options = edge.load_app_options("config/host.json")

        # Create DI container and get dispatcher
        dispatcher = create_service_provider(app_options)

        # Use dispatcher in application
        app = edge.EdgeApp(dispatcher)
        ```
    """
    from .service_provider import ServiceProvider

    io_c_container = ServiceProvider()
    io_c_container.add_singleton(ServiceProvider, instance=io_c_container)
    io_c_container.add_singleton(
        IServiceContainer, instance=io_c_container)
    io_c_container.add_singleton(IServiceProvider, instance=io_c_container)

    # Create or get event loop
    if loop is None and sys.platform == 'win32':
        # By default Windows can use only 64 sockets in asyncio loop. This is a limitation of underlying select() API call.
        # Use Windows version of proactor event loop using IOCP
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    event_loop = asyncio.get_event_loop() if loop is None else loop

    # Register event loop in DI container
    return io_c_container.add_singleton(
        asyncio.AbstractEventLoop, instance=event_loop)
