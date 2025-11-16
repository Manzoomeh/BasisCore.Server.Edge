"""
Dependency Injection Example - Simple DI Usage

This example demonstrates how to use the Dependency Injection container
with BasisCore.Edge web server.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from bclib import edge
from bclib.context import RESTfulContext
from bclib.service_provider import ServiceProvider

# ==================== Service Interfaces ====================


class ILogger(ABC):
    """Logger service interface"""

    @abstractmethod
    def log(self, message: str):
        """Log a message"""
        pass


class ITimeService(ABC):
    """Time service interface"""

    @abstractmethod
    def get_current_time(self) -> str:
        """Get current time as string"""
        pass


class IGreetingService(ABC):
    """Greeting service interface"""

    @abstractmethod
    def greet(self, name: str) -> str:
        """Generate greeting message"""
        pass


# ==================== Service Implementations ====================

class ConsoleLogger(ILogger):
    """Console logger implementation"""

    def __init__(self):
        self.log_count = 0
        print("[ConsoleLogger] Instance created")

    def log(self, message: str):
        self.log_count += 1
        print(f"[LOG #{self.log_count}] {message}")


class TimeService(ITimeService):
    """Time service implementation"""

    def __init__(self):
        print("[TimeService] Instance created")

    def get_current_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class GreetingService(IGreetingService):
    """Greeting service with dependencies"""

    def __init__(self, logger: ILogger, time_service: ITimeService):
        self.logger = logger
        self.time_service = time_service
        self.logger.log("GreetingService initialized")

    def greet(self, name: str) -> str:
        current_time = self.time_service.get_current_time()
        greeting = f"Hello {name}! Current time is {current_time}"
        self.logger.log(f"Generated greeting for {name}")
        return greeting


# ==================== Custom Dispatcher with DI ====================

class DIDispatcher(edge.DevServerDispatcher):
    """Custom dispatcher that configures DI services"""

    def __init__(self, options):
        super().__init__(options)

        """Configure dependency injection services"""

        print("\n" + "=" * 60)
        print("Configuring Dependency Injection Services")
        print("=" * 60)

        # Singleton services (one instance for entire application)
        self.services.add_singleton(ILogger, ConsoleLogger)
        self.services.add_singleton(ITimeService, TimeService)

        # Transient services (new instance every time)
        # Note: We use factory to inject dependencies
        def __init__(self, options: dict = None):
        super().__init__(options)
        # Register services
        self.add_singleton(ILogger, ConsoleLogger)
        self.add_singleton(ITimeService, TimeService)

        # Different lifetime - Transient means new instance every time
        # Example showing factory function
        self.add_transient(
            IGreetingService,
            factory=lambda: GreetingService(
                logger=self.services.get_service(ILogger),
                time_service=self.services.get_service(ITimeService)
            )
        )

        print("✓ Services registered successfully")
        print("=" * 60 + "\n")


# Create custom options
options = {
    "server": "localhost:8092",
    "router": "restful"
}

# Create dispatcher with DI
app = DIDispatcher(options)


# ==================== Handlers ====================

@app.restful_action()
async def hello(context: RESTfulContext):
    """
    Simple hello endpoint

    GET http://localhost:8092/hello
    """
    # Get services from DI container
    logger = context.get_service(ILogger)
    time_service = context.get_service(ITimeService)

    if logger:
        logger.log("Processing /hello request")

    current_time = time_service.get_current_time() if time_service else "Unknown"

    return {
        "message": "Hello from Dependency Injection!",
        "time": current_time,
        "endpoint": "/hello"
    }


@app.restful_action("/greet/:name")
async def greet(context: RESTfulContext):
    """
    Greeting endpoint with parameter

    GET http://localhost:8092/greet/John
    GET http://localhost:8092/greet/Sarah
    """
    # Get services from DI container
    logger = context.get_service(ILogger)
    greeting_service = context.get_service(IGreetingService)

    # Get name from URL
    name = context.url_segments.name

    if logger:
        logger.log(f"Processing /greet request for {name}")

    # Use greeting service
    greeting_message = greeting_service.greet(
        name) if greeting_service else f"Hello {name}!"

    return {
        "greeting": greeting_message,
        "name": name
    }


@app.restful_action("/services/info")
async def services_info(context: RESTfulContext):
    """
    Show information about registered services

    GET http://localhost:8092/services/info
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Processing /services/info request")

    # Get service provider info
    services = context.services

    return {
        "message": "Dependency Injection Information",
        "services_available": services is not None,
        "registered_services": [
            {
                "interface": "ILogger",
                "implementation": "ConsoleLogger",
                "lifetime": "Singleton"
            },
            {
                "interface": "ITimeService",
                "implementation": "TimeService",
                "lifetime": "Singleton"
            },
            {
                "interface": "IGreetingService",
                "implementation": "GreetingService",
                "lifetime": "Transient"
            }
        ],
        "description": "Services are injected into handlers via context.get_service()"
    }


@app.restful_action("/test/singleton")
async def test_singleton(context: RESTfulContext):
    """
    Test singleton lifetime - same instance across requests

    GET http://localhost:8092/test/singleton
    """
    logger = context.get_service(ILogger)

    if logger and isinstance(logger, ConsoleLogger):
        logger.log("Testing singleton service")

        return {
            "message": "Singleton Test",
            "log_count": logger.log_count,
            "note": "log_count increases across requests (same instance)"
        }

    return {"error": "Logger not available"}


@app.restful_action("/test/transient")
async def test_transient(context: RESTfulContext):
    """
    Test transient lifetime - new instance every time

    GET http://localhost:8092/test/transient
    """
    logger = context.get_service(ILogger)

    # Get greeting service multiple times
    greeting1 = context.get_service(IGreetingService)
    greeting2 = context.get_service(IGreetingService)

    if logger:
        logger.log("Testing transient service")

    return {
        "message": "Transient Test",
        "greeting1_id": id(greeting1),
        "greeting2_id": id(greeting2),
        "are_same": greeting1 is greeting2,
        "note": "Transient services create new instances each time (different IDs)"
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Dependency Injection Example Server")
    print("=" * 60)
    print()
    print("Server URL: http://localhost:8092")
    print()
    print("Available Endpoints:")
    print("  GET /hello")
    print("  GET /greet/:name")
    print("  GET /services/info")
    print("  GET /test/singleton")
    print("  GET /test/transient")
    print()
    print("Example URLs:")
    print("  - http://localhost:8092/hello")
    print("  - http://localhost:8092/greet/John")
    print("  - http://localhost:8092/services/info")
    print("  - http://localhost:8092/test/singleton")
    print("  - http://localhost:8092/test/transient")
    print()
    print("=" * 60)
    print()

    app.listening()
