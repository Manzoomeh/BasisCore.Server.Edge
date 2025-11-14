"""
Automatic DI Injection in Handlers

This example shows how dependency injection works automatically in handlers.
Services are injected based on type hints without manually calling get_service().
"""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext
from bclib.utility import ServiceProvider

# ==================== Service Interfaces ====================


class ILogger(ABC):
    """Logger service interface"""

    @abstractmethod
    def log(self, message: str, level: str = "INFO"):
        pass


class ITimeService(ABC):
    """Time service interface"""

    @abstractmethod
    def get_current_time(self) -> str:
        pass


class IUserService(ABC):
    """User service interface"""

    @abstractmethod
    def get_user(self, user_id: str) -> dict:
        pass


# ==================== Implementations ====================

class ConsoleLogger(ILogger):
    """Console logger implementation"""

    def __init__(self):
        self.log_count = 0
        print("[ConsoleLogger] Created")

    def log(self, message: str, level: str = "INFO"):
        self.log_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] #{self.log_count}: {message}")


class TimeService(ITimeService):
    """Time service implementation"""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self.logger.log("TimeService initialized")

    def get_current_time(self) -> str:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logger.log(f"Time requested: {time_str}", "DEBUG")
        return time_str


class UserService(IUserService):
    """User service implementation"""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self.users = {
            "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
            "2": {"id": "2", "name": "Bob", "email": "bob@example.com"},
            "3": {"id": "3", "name": "Charlie", "email": "charlie@example.com"}
        }
        self.logger.log("UserService initialized with sample users")

    def get_user(self, user_id: str) -> dict:
        self.logger.log(f"Getting user: {user_id}")
        return self.users.get(user_id, {"error": "User not found"})


# ==================== Setup ====================

options = {
    "server": "localhost:8096",
    "router": "restful",
    "log_errors": True
}

app = edge.DevServerDispatcher(options)

# Configure services directly
print("\n" + "=" * 70)
print("Configuring Services for Automatic DI Injection")
print("=" * 70)

app.services.add_singleton(ILogger, ConsoleLogger)
app.services.add_singleton(ITimeService, TimeService)
app.services.add_transient(IUserService, UserService)

print("✓ Services configured")
print("=" * 70 + "\n")


# ==================== Handlers with Automatic DI ====================

@app.restful_action(app.url("with-logger"))
async def with_logger(context: RESTfulContext, logger: ILogger):
    """
    Handler with automatic logger injection

    Notice: logger parameter is automatically injected!
    No need to call context.get_service(ILogger)

    GET http://localhost:8096/with-logger
    """
    # Logger is automatically injected based on type hint
    logger.log("Handler called with automatic DI!")

    return {
        "message": "Logger was automatically injected!",
        "note": "No context.get_service() needed",
        "log_count": logger.log_count
    }


@app.restful_action(app.url("with-time"))
async def with_time(context: RESTfulContext, time_service: ITimeService):
    """
    Handler with automatic time service injection

    GET http://localhost:8096/with-time
    """
    # TimeService is automatically injected
    current_time = time_service.get_current_time()

    return {
        "message": "Time service automatically injected",
        "current_time": current_time,
        "note": "TimeService has ILogger dependency - also auto-injected!"
    }


@app.restful_action(app.url("user/:id"))
async def get_user(
    context: RESTfulContext,
    logger: ILogger,
    user_service: IUserService
):
    """
    Handler with multiple automatic injections

    Notice: Both logger and user_service are automatically injected!

    GET http://localhost:8096/user/1
    GET http://localhost:8096/user/2
    GET http://localhost:8096/user/99
    """
    user_id = context.url_segments.id

    # Both services automatically injected!
    logger.log(f"Getting user {user_id} via automatic DI")
    user = user_service.get_user(user_id)

    return {
        "user": user,
        "note": "Both ILogger and IUserService were automatically injected!"
    }


@app.restful_action(app.url("complex"))
async def complex_handler(
    context: RESTfulContext,
    logger: ILogger,
    time_service: ITimeService,
    user_service: IUserService
):
    """
    Handler with multiple services automatically injected

    GET http://localhost:8096/complex
    """
    logger.log("Complex handler with 3 auto-injected services")

    current_time = time_service.get_current_time()
    user = user_service.get_user("1")

    return {
        "message": "Multiple services automatically injected",
        "services_injected": ["ILogger", "ITimeService", "IUserService"],
        "current_time": current_time,
        "sample_user": user,
        "note": "All services injected automatically based on type hints!"
    }


@app.restful_action(app.url("mixed/:name"))
async def mixed_parameters(
    context: RESTfulContext,
    logger: ILogger,
    time_service: ITimeService
):
    """
    Handler with both context and injected services

    GET http://localhost:8096/mixed/Alice
    """
    # Get data from context (URL parameter)
    name = context.url_segments.name

    # Use injected services
    logger.log(f"Processing request for {name}")
    current_time = time_service.get_current_time()

    return {
        "greeting": f"Hello {name}!",
        "time": current_time,
        "note": "Mixed: URL param from context, services auto-injected"
    }


@app.restful_action(app.url("comparison"))
async def comparison(context: RESTfulContext):
    """
    Show comparison between old and new way

    GET http://localhost:8096/comparison
    """
    return {
        "title": "Automatic DI Injection vs Manual",
        "old_way": {
            "code": """
@app.restful_action()
async def handler(context: RESTfulContext):
    logger = context.get_service(ILogger)
    db = context.get_service(IDatabase)
    
    if logger:
        logger.log("Processing...")
    if db:
        result = await db.query("SELECT ...")
    
    return {"data": result}
""",
            "issues": [
                "Must manually call get_service()",
                "Need null checks",
                "Verbose code",
                "Easy to forget services"
            ]
        },
        "new_way": {
            "code": """
@app.restful_action()
async def handler(
    context: RESTfulContext,
    logger: ILogger,
    db: IDatabase
):
    logger.log("Processing...")
    result = await db.query("SELECT ...")
    return {"data": result}
""",
            "benefits": [
                "✅ Automatic injection based on type hints",
                "✅ No manual get_service() calls",
                "✅ No null checks needed",
                "✅ Cleaner, more readable code",
                "✅ IDE autocomplete works better",
                "✅ Explicit dependencies in signature"
            ]
        },
        "how_it_works": [
            "1. Dispatcher reads handler signature",
            "2. Extracts type hints for parameters",
            "3. Resolves services from DI container",
            "4. Injects services when calling handler",
            "5. Handler receives both context and services"
        ]
    }


@app.restful_action(app.url("info"))
async def info(context: RESTfulContext, logger: ILogger):
    """
    Information about automatic DI injection

    GET http://localhost:8096/info
    """
    logger.log("Showing automatic DI info")

    return {
        "title": "Automatic Dependency Injection in Handlers",
        "description": "Services are automatically injected based on type hints",
        "usage": "Just add type-hinted parameters to your handler function",
        "example": "async def handler(context: RESTfulContext, logger: ILogger):",
        "features": [
            "Automatic injection based on parameter type hints",
            "Works with all handler decorators (@restful_action, @web_action, etc.)",
            "Context always provided as first parameter",
            "Additional services injected from DI container",
            "No manual service resolution needed"
        ],
        "requirements": [
            "Services must be registered in DI container",
            "Parameters must have type hints",
            "Type must match interface in DI container"
        ],
        "benefits": [
            "Less boilerplate code",
            "Better readability",
            "Explicit dependencies",
            "Easier testing (mock services)",
            "IDE support for autocomplete"
        ]
    }


@app.restful_action()
async def hello(context: RESTfulContext):
    """
    Simple handler - no DI needed

    GET http://localhost:8096/hello
    """
    return {
        "message": "Hello! This endpoint doesn't use DI",
        "time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Automatic DI Injection Example")
    print("=" * 70)
    print()
    print("Server URL: http://localhost:8096")
    print()
    print("Key Feature: Automatic Dependency Injection in Handlers")
    print("  - Add type-hinted parameters to handlers")
    print("  - Services automatically injected from DI container")
    print("  - No manual get_service() calls needed")
    print()
    print("Available Endpoints:")
    print("  GET /hello")
    print("  GET /with-logger (auto-injects ILogger)")
    print("  GET /with-time (auto-injects ITimeService)")
    print("  GET /user/:id (auto-injects ILogger + IUserService)")
    print("  GET /complex (auto-injects 3 services)")
    print("  GET /mixed/:name (context + auto-injected services)")
    print("  GET /comparison (old vs new way)")
    print("  GET /info")
    print()
    print("Example URLs:")
    print("  - http://localhost:8096/hello")
    print("  - http://localhost:8096/with-logger")
    print("  - http://localhost:8096/with-time")
    print("  - http://localhost:8096/user/1")
    print("  - http://localhost:8096/complex")
    print("  - http://localhost:8096/mixed/Alice")
    print("  - http://localhost:8096/comparison")
    print("  - http://localhost:8096/info")
    print()
    print("=" * 70)
    print()

    app.listening()
