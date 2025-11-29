"""
Demo: Register services directly through Dispatcher
Shows simplified service registration using dispatcher.add_*() methods
"""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext

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
        print("[ConsoleLogger] Created")

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [LOG] {message}")


class TimeService(ITimeService):
    def __init__(self):
        print("[TimeService] Created")

    def get_current_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class GreetingService(IGreetingService):
    def __init__(self):
        print("[GreetingService] Created (Transient)")

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

# ==================== Application Setup ====================


app = edge.from_options({
    "http": "localhost:8098",
    "router": "restful",
    "name": "dispatcher_di_demo"
})

# ==================== Configure Services ====================


def configure_services():
    """Configure DI services"""
    print("=" * 70)
    print("Configuring Services via Dispatcher")
    print("=" * 70)

    # Register services directly through dispatcher methods
    app.add_singleton(ILogger, ConsoleLogger)
    app.add_singleton(ITimeService, TimeService)
    app.add_transient(IGreetingService, GreetingService)

    print("✓ Services configured using dispatcher methods")
    print("  - dispatcher.add_singleton(ILogger, ConsoleLogger)")
    print("  - dispatcher.add_singleton(ITimeService, TimeService)")
    print("  - dispatcher.add_transient(IGreetingService, GreetingService)")
    print("=" * 70)
    print()

# ==================== Handlers with Automatic DI ====================


@app.restful_handler()
def hello_handler(logger: ILogger):
    """Handler with only logger - no context needed"""
    logger.log("Hello endpoint called")
    return {"message": "Hello from dispatcher DI!"}


@app.restful_handler()
def time_handler(time_service: ITimeService, logger: ILogger):
    """Handler with multiple services injected"""
    logger.log("Time endpoint called")
    current_time = time_service.get_current_time()
    return {
        "message": "Current time",
        "time": current_time
    }


@app.restful_handler()
def greet_handler(greeting: IGreetingService, logger: ILogger):
    """Handler with transient service (new instance each time)"""
    logger.log("Greet endpoint called")
    message = greeting.greet("Developer")
    return {"greeting": message}


@app.restful_handler()
def mixed_handler(context: RESTfulContext, time_service: ITimeService, logger: ILogger):
    """Handler with context AND injected services"""
    logger.log(f"Mixed endpoint called: {context.url}")
    current_time = time_service.get_current_time()
    return {
        "url": context.url,
        "time": current_time,
        "message": "Mix of context and DI services"
    }


@app.restful_handler()
def info_handler():
    """Handler with no dependencies at all"""
    return {
        "message": "Dispatcher Service Registration Demo",
        "features": [
            "dispatcher.add_singleton()",
            "dispatcher.add_scoped()",
            "dispatcher.add_transient()",
            "Direct service registration on dispatcher"
        ]
    }

# ==================== Application ====================


if __name__ == "__main__":
    print()
    print("=" * 70)
    print("Dispatcher Service Registration Demo")
    print("=" * 70)
    print()
    print("Server URL: http://localhost:8098")
    print()
    print("Key Feature: Register services directly on dispatcher")
    print("  - dispatcher.add_singleton()")
    print("  - dispatcher.add_scoped()")
    print("  - dispatcher.add_transient()")
    print("  - Fluent API with method chaining")
    print()
    print("Available Endpoints:")
    print("  GET /hello (logger only)")
    print("  GET /time (time service + logger)")
    print("  GET /greet (greeting service + logger - transient)")
    print("  GET /mixed (context + services)")
    print("  GET /info (no dependencies)")
    print()
    print("Example URLs:")
    print("  - http://localhost:8098/hello")
    print("  - http://localhost:8098/time")
    print("  - http://localhost:8098/greet")
    print("  - http://localhost:8098/mixed")
    print("  - http://localhost:8098/info")
    print()
    print("=" * 70)
    print()

    configure_services()
    app.listening()
