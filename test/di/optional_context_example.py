"""Example: Optional Context in RESTful Handlers"""
from abc import ABC, abstractmethod

from bclib import edge
from bclib.context import RESTfulContext
from bclib.utility import ServiceProvider


# Services
class ILogger(ABC):
    @abstractmethod
    def log(self, level: str, message: str):
        pass


class ConsoleLogger(ILogger):
    def __init__(self):
        print("[ConsoleLogger] Created")

    def log(self, level: str, message: str):
        print(f"[{level}] {message}")


class ITimeService(ABC):
    @abstractmethod
    def get_current_time(self) -> str:
        pass


class TimeService(ITimeService):
    def __init__(self):
        print("[TimeService] Created")

    def get_current_time(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Create dispatcher using edge module
app = edge.from_options({
    "host": "localhost",
    "port": 8097,
    "url": "http://localhost:8097"
})

# Setup DI


def configure_di(services: ServiceProvider):
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_transient(ITimeService, TimeService)


app.configure_services(configure_di)


# Handlers with different signatures

@app.restful_action()
def handler_with_context(context: RESTfulContext):
    """Traditional handler - still works!"""
    return {
        "message": "Handler with context",
        "url": context.url.path if hasattr(context, 'url') else "N/A"
    }


@app.restful_action()
def handler_no_context(logger: ILogger):
    """New style - no context needed!"""
    logger.log("INFO", "Handler called without context parameter!")
    return {
        "message": "No context parameter needed",
        "style": "clean and simple"
    }


@app.restful_action()
def handler_with_services(logger: ILogger, time: ITimeService):
    """Multiple services, no context"""
    current_time = time.get_current_time()
    logger.log("INFO", f"Time requested: {current_time}")
    return {
        "message": "Services only",
        "current_time": current_time
    }


@app.restful_action()
def handler_mixed(context: RESTfulContext, logger: ILogger, time: ITimeService):
    """Mix of context and services"""
    logger.log(
        "INFO", f"Mixed handler called for: {context.url.path if hasattr(context, 'url') else 'N/A'}")
    return {
        "message": "Context + Services",
        "time": time.get_current_time(),
        "path": context.url.path if hasattr(context, 'url') else "N/A"
    }


@app.restful_action()
async def async_handler_no_context(logger: ILogger):
    """Async handler without context"""
    logger.log("INFO", "Async handler without context!")
    return {
        "message": "Async + No Context",
        "async": True
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Optional Context Example - RESTful Handlers")
    print("=" * 70)
    print("\nAvailable endpoints:")
    print("  GET http://localhost:8097/handler_with_context")
    print("  GET http://localhost:8097/handler_no_context")
    print("  GET http://localhost:8097/handler_with_services")
    print("  GET http://localhost:8097/handler_mixed")
    print("  GET http://localhost:8097/async_handler_no_context")
    print("\nFeature: Context is now optional!")
    print("  - Handlers can skip context parameter if not needed")
    print("  - Only request services you actually use")
    print("  - Cleaner, more focused handler signatures")
    print("=" * 70)
    print()

    try:
        app.listening()
    except KeyboardInterrupt:
        print("\nServer stopped.")
