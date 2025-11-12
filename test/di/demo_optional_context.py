"""
Demo: Optional Context Parameter in Handlers

This example demonstrates the new optional context feature where handlers
can choose whether to receive the context parameter or not.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext

# ==================== Services ====================


class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass


class ConsoleLogger(ILogger):
    def __init__(self):
        print("[ConsoleLogger] Initialized")

    def log(self, message: str):
        print(f"[LOG] {message}")


class ITimeService(ABC):
    @abstractmethod
    def get_time(self) -> str:
        pass


class TimeService(ITimeService):
    def get_time(self) -> str:
        return datetime.now().strftime("%H:%M:%S")


# ==================== Create App ====================

options = {
    "server": "localhost:8098",
    "router": "restful"
}

app = edge.DevServerDispatcher(options)


# Configure DI
def setup_services(services):
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_transient(ITimeService, TimeService)


app.configure_services(setup_services)


# ==================== Handlers ====================

@app.restful_action()
def traditional_handler(context: RESTfulContext):
    """Traditional way - still works perfectly!"""
    return {
        "style": "traditional",
        "message": "Handler with context parameter",
        "has_context": True
    }


@app.restful_action()
def clean_handler(logger: ILogger, time: ITimeService):
    """New way - no context needed!"""
    logger.log(f"Clean handler called at {time.get_time()}")
    return {
        "style": "clean",
        "message": "No context parameter needed!",
        "time": time.get_time()
    }


@app.restful_action()
def logger_only(logger: ILogger):
    """Minimal handler - just one service"""
    logger.log("Minimal handler with only logger")
    return {
        "style": "minimal",
        "message": "Only logger injected"
    }


@app.restful_action()
def mixed_handler(context: RESTfulContext, logger: ILogger, time: ITimeService):
    """Mix of old and new - context + services"""
    logger.log(f"Mixed handler at {time.get_time()}")
    return {
        "style": "mixed",
        "message": "Context + multiple services",
        "time": time.get_time(),
        "has_context": True
    }


@app.restful_action()
async def async_clean(logger: ILogger):
    """Async handler without context"""
    logger.log("Async handler without context!")
    return {
        "style": "async_clean",
        "message": "Async + no context",
        "async": True
    }


@app.restful_action()
def comparison():
    """Show the difference"""
    return {
        "old_way": {
            "signature": "def handler(context: RESTfulContext)",
            "description": "Always receive context, manually get services",
            "example": "logger = context.services.get_service(ILogger)"
        },
        "new_way": {
            "signature": "def handler(logger: ILogger, db: IDatabase)",
            "description": "Context optional, services auto-injected",
            "example": "Just use the injected parameters!"
        },
        "benefits": [
            "Cleaner handler signatures",
            "Only request what you need",
            "Better testability",
            "Backward compatible"
        ]
    }


# ==================== Main ====================

if __name__ == "__main__":
    print("=" * 70)
    print("Optional Context Parameter Demo")
    print("=" * 70)
    print("\nServer running at http://localhost:8098")
    print("\nAvailable endpoints:")
    print("  GET /traditional_handler  - Traditional with context")
    print("  GET /clean_handler        - New style (no context)")
    print("  GET /logger_only          - Minimal (only logger)")
    print("  GET /mixed_handler        - Mixed (context + services)")
    print("  GET /async_clean          - Async without context")
    print("  GET /comparison           - Compare old vs new")
    print("\n✨ Feature Highlights:")
    print("  • Context parameter is now OPTIONAL")
    print("  • Handlers choose what they need")
    print("  • Services auto-injected by type")
    print("  • Fully backward compatible")
    print("=" * 70)
    print()

    try:
        app.listening()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
