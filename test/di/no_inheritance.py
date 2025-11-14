"""
DI without Inheritance Example

This example shows how to use Dependency Injection WITHOUT creating a derived dispatcher class.
Perfect for simple applications or quick prototypes.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext
from bclib.utility import ServiceProvider

# ==================== Service Interfaces ====================


class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass


class ITimeService(ABC):
    @abstractmethod
    def get_current_time(self) -> str:
        pass


class IGreetingService(ABC):
    @abstractmethod
    def greet(self, name: str) -> str:
        pass


# ==================== Implementations ====================

class ConsoleLogger(ILogger):
    def __init__(self):
        self.log_count = 0
        print("[ConsoleLogger] Created")

    def log(self, message: str):
        self.log_count += 1
        print(f"[{self.log_count}] {message}")


class TimeService(ITimeService):
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.logger.log("TimeService initialized")

    def get_current_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class GreetingService(IGreetingService):
    def __init__(self, logger: ILogger, time_service: ITimeService):
        self.logger = logger
        self.time_service = time_service
        self.logger.log("GreetingService initialized")

    def greet(self, name: str) -> str:
        current_time = self.time_service.get_current_time()
        greeting = f"Hello {name}! Time: {current_time}"
        self.logger.log(f"Greeted: {name}")
        return greeting


# ==================== Setup WITHOUT Inheritance ====================

options = {
    "server": "localhost:8095",
    "router": "restful"
}

# Create dispatcher directly - NO INHERITANCE!
app = edge.from_options(options)


# Method 1: Using named function
def setup_services(services: ServiceProvider):
    """
    Configure services using a regular function
    No need to create a class!
    """
    print("\n" + "=" * 70)
    print("Configuring Services WITHOUT Inheritance")
    print("=" * 70)

    # Register services with constructor injection
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_singleton(ITimeService, TimeService)
    services.add_transient(IGreetingService, GreetingService)

    print("✓ Services configured directly")
    print("=" * 70 + "\n")


# Configure services directly WITHOUT creating derived class!
setup_services(app.services)


# ==================== Handlers ====================

@app.restful_action()
async def hello(context: RESTfulContext):
    """
    Simple hello endpoint

    GET http://localhost:8095/hello
    """
    logger = context.get_service(ILogger)
    time_service = context.get_service(ITimeService)

    if logger:
        logger.log("Processing /hello")

    return {
        "message": "DI without Inheritance!",
        "time": time_service.get_current_time() if time_service else "N/A",
        "note": "No dispatcher inheritance needed!"
    }


@app.restful_action("/greet/:name")
async def greet(context: RESTfulContext):
    """
    Greeting with DI

    GET http://localhost:8095/greet/Alice
    GET http://localhost:8095/greet/Bob
    """
    name = context.url_segments.name
    greeting_service = context.get_service(IGreetingService)

    if not greeting_service:
        return {"error": "Service not available"}

    greeting = greeting_service.greet(name)

    return {
        "greeting": greeting,
        "method": "No inheritance required!"
    }


@app.restful_action("/info")
async def info(context: RESTfulContext):
    """
    Show information about no-inheritance DI

    GET http://localhost:8095/info
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Showing info")

    return {
        "title": "Dependency Injection Without Inheritance",
        "description": "Configure services without creating a derived dispatcher class",
        "methods": [
            {
                "method": "app.services.add_*()",
                "description": "Directly register services on dispatcher's service provider",
                "example": "app.services.add_singleton(ILogger, ConsoleLogger)"
            }
        ],
        "benefits": [
            "✅ No need to create derived classes",
            "✅ Simpler for small applications",
            "✅ Quick prototyping",
            "✅ Easy to understand",
            "✅ Less boilerplate code"
        ],
        "comparison": {
            "with_inheritance": {
                "code": "class MyDispatcher(edge.DevServerDispatcher):\n    def __init__(self, options):\n        super().__init__(options)\n        self.services.add_singleton(...)",
                "lines": "Multiple lines, class definition"
            },
            "without_inheritance": {
                "code": "app.services.add_singleton(...)",
                "lines": "Single line, no class needed"
            }
        },
        "use_cases": [
            "Small applications",
            "Prototypes and demos",
            "Simple REST APIs",
            "Learning DI concepts",
            "When you don't need custom dispatcher logic"
        ],
        "when_to_use_inheritance": [
            "Large applications with custom dispatcher logic",
            "When you need to override dispatcher methods",
            "Complex initialization requirements",
            "Team prefers OOP patterns"
        ]
    }


@app.restful_action("/test/chaining")
async def test_chaining(context: RESTfulContext):
    """
    Test method chaining

    GET http://localhost:8095/test/chaining
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Testing method chaining")

    return {
        "message": "Direct Service Registration",
        "note": "Services can be registered directly via app.services",
        "example": "app.services.add_singleton(ILogger, ConsoleLogger)",
        "benefit": "Simple and straightforward service registration"
    }


if __name__ == "__main__":
    print("=" * 70)
    print("DI Without Inheritance Example")
    print("=" * 70)
    print()
    print("Server URL: http://localhost:8095")
    print()
    print("Key Feature: Configure DI WITHOUT Creating Derived Class")
    print("  - Use app.services.add_singleton/scoped/transient() directly")
    print("  - No inheritance needed")
    print("  - Perfect for simple applications")
    print()
    print("Available Endpoints:")
    print("  GET /hello")
    print("  GET /greet/:name")
    print("  GET /info")
    print("  GET /test/chaining")
    print()
    print("Example URLs:")
    print("  - http://localhost:8095/hello")
    print("  - http://localhost:8095/greet/Alice")
    print("  - http://localhost:8095/info")
    print("  - http://localhost:8095/test/chaining")
    print()
    print("Comparison:")
    print("  ❌ Old way: class MyDispatcher with __init__ override")
    print("  ✅ New way: app.services.add_singleton(...) directly")
    print()
    print("=" * 70)
    print()

    app.listening()
