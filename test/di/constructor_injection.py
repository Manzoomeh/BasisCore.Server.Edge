"""
Constructor Injection Example

This example demonstrates automatic dependency injection using type hints.
Services are automatically resolved and injected into constructor parameters.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext
from bclib.service_provider import ServiceProvider

# ==================== Service Interfaces ====================


class ILogger(ABC):
    """Logger service interface"""

    @abstractmethod
    def log(self, message: str, level: str = "INFO"):
        pass


class IConfig(ABC):
    """Configuration service interface"""

    @abstractmethod
    def get(self, key: str) -> str:
        pass


class ITimeService(ABC):
    """Time service interface"""

    @abstractmethod
    def get_current_time(self) -> str:
        pass


# ==================== Basic Service Implementations ====================

class ConsoleLogger(ILogger):
    """Console logger - will be injected as singleton"""

    def __init__(self):
        self.log_count = 0
        print("[ConsoleLogger] Created")

    def log(self, message: str, level: str = "INFO"):
        self.log_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")


class SimpleConfig(IConfig):
    """Simple configuration service"""

    def __init__(self):
        self.data = {
            "app_name": "Constructor Injection Demo",
            "version": "1.0.0",
            "environment": "development"
        }
        print("[SimpleConfig] Created")

    def get(self, key: str) -> str:
        return self.data.get(key, "")


class TimeService(ITimeService):
    """Time service with constructor injection"""

    def __init__(self, logger: ILogger, config: IConfig):
        """Constructor with type hints - dependencies auto-injected"""
        self.logger = logger
        self.config = config

        app_name = config.get("app_name")
        self.logger.log(f"TimeService initialized for {app_name}")

    def get_current_time(self) -> str:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.log(f"Time requested: {time_str}", "DEBUG")
        return time_str


# ==================== Complex Service with Multiple Dependencies ====================

class ReportService:
    """
    Report service with multiple injected dependencies

    Notice: No manual service resolution needed!
    Type hints automatically resolve dependencies.
    """

    def __init__(
        self,
        logger: ILogger,           # Injected from DI
        config: IConfig,           # Injected from DI
        time_service: ITimeService  # Injected from DI
    ):
        """All parameters automatically injected based on type hints"""
        self.logger = logger
        self.config = config
        self.time_service = time_service

        self.logger.log("ReportService initialized with all dependencies")

    def generate_report(self, report_type: str) -> dict:
        """Generate a report"""
        self.logger.log(f"Generating {report_type} report...")

        return {
            "report_type": report_type,
            "app_name": self.config.get("app_name"),
            "version": self.config.get("version"),
            "generated_at": self.time_service.get_current_time(),
            "status": "success"
        }


class UserService:
    """User service with optional dependencies"""

    def __init__(
        self,
        logger: ILogger,
        config: IConfig
    ):
        self.logger = logger
        self.config = config
        self.logger.log("UserService initialized")

    def get_user_info(self, user_id: str) -> dict:
        """Get user information"""
        self.logger.log(f"Fetching user info for: {user_id}")

        return {
            "user_id": user_id,
            "app_name": self.config.get("app_name"),
            "environment": self.config.get("environment")
        }


# ==================== Dispatcher with Constructor Injection ====================

class ConstructorInjectionDispatcher(edge.DevServerDispatcher):
    """Dispatcher that demonstrates constructor injection"""

    def __init__(self, options):
        super().__init__(options)

        """Configure services - notice how simple the registration is now!"""

        print("\n" + "=" * 70)
        print("Configuring Constructor Injection Services")
        print("=" * 70)

        # Register base services (singleton)
        self.services.add_singleton(ILogger, ConsoleLogger)
        self.services.add_singleton(IConfig, SimpleConfig)

        # Register TimeService - dependencies auto-injected from constructor!
        self.services.add_singleton(ITimeService, TimeService)

        # Register complex services - all dependencies auto-resolved!
        self.services.add_transient(ReportService)
        self.services.add_transient(UserService)

        print("✓ All services registered with automatic constructor injection")
        print("=" * 70 + "\n")


# Create dispatcher
options = {
    "server": "localhost:8093",
    "router": "restful"
}

app = ConstructorInjectionDispatcher(options)


# ==================== Handlers ====================

@app.restful_action()
async def hello(context: RESTfulContext):
    """
    Test constructor injection

    GET http://localhost:8093/hello
    """
    logger = context.get_service(ILogger)
    time_service = context.get_service(ITimeService)

    if logger:
        logger.log("Processing /hello request")

    current_time = time_service.get_current_time() if time_service else "Unknown"

    return {
        "message": "Constructor Injection Demo",
        "time": current_time,
        "note": "TimeService has ILogger and IConfig auto-injected!"
    }


@app.restful_action("/report/:type")
async def generate_report(context: RESTfulContext):
    """
    Generate report using service with multiple dependencies

    GET http://localhost:8093/report/daily
    GET http://localhost:8093/report/weekly
    """
    report_service = context.get_service(ReportService)

    if not report_service:
        return {"error": "ReportService not available"}

    report_type = context.url_segments.type
    report = report_service.generate_report(report_type)

    return {
        "report": report,
        "note": "ReportService has 3 dependencies auto-injected via constructor!"
    }


@app.restful_action("/user/:id")
async def get_user(context: RESTfulContext):
    """
    Get user information

    GET http://localhost:8093/user/12345
    GET http://localhost:8093/user/98765
    """
    user_service = context.get_service(UserService)

    if not user_service:
        return {"error": "UserService not available"}

    user_id = context.url_segments.id
    user_info = user_service.get_user_info(user_id)

    return {
        "user": user_info,
        "note": "UserService dependencies auto-injected!"
    }


@app.restful_action("/injection/info")
async def injection_info(context: RESTfulContext):
    """
    Show information about constructor injection

    GET http://localhost:8093/injection/info
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Showing constructor injection info")

    return {
        "title": "Constructor Injection with Type Hints",
        "description": "Dependencies are automatically resolved from type hints",
        "how_it_works": [
            "1. Define constructor with type hints: def __init__(self, logger: ILogger)",
            "2. Register service: services.add_transient(MyService)",
            "3. ServiceProvider reads type hints using inspect and get_type_hints()",
            "4. Dependencies are automatically resolved from DI container",
            "5. Instance created with all dependencies injected"
        ],
        "benefits": [
            "No manual factory functions needed",
            "Clean, readable code",
            "Type-safe dependency resolution",
            "Easier to add new dependencies",
            "Better IDE support and autocomplete"
        ],
        "example": {
            "before": "services.add_transient(TimeService, factory=lambda: TimeService(logger=services.get_service(ILogger), config=services.get_service(IConfig)))",
            "after": "services.add_transient(TimeService)"
        },
        "registered_services": [
            {
                "service": "ILogger → ConsoleLogger",
                "lifetime": "Singleton",
                "dependencies": []
            },
            {
                "service": "IConfig → SimpleConfig",
                "lifetime": "Singleton",
                "dependencies": []
            },
            {
                "service": "ITimeService → TimeService",
                "lifetime": "Singleton",
                "dependencies": ["ILogger", "IConfig"]
            },
            {
                "service": "ReportService",
                "lifetime": "Transient",
                "dependencies": ["ILogger", "IConfig", "ITimeService"]
            },
            {
                "service": "UserService",
                "lifetime": "Transient",
                "dependencies": ["ILogger", "IConfig"]
            }
        ]
    }


@app.restful_action("/test/dependency-chain")
async def test_dependency_chain(context: RESTfulContext):
    """
    Test complex dependency chain

    GET http://localhost:8093/test/dependency-chain
    """
    logger = context.get_service(ILogger)

    if logger:
        logger.log("Testing dependency chain...")

    # Get services - watch console to see injection order
    time_service = context.get_service(ITimeService)
    report_service = context.get_service(ReportService)

    if not (time_service and report_service):
        return {"error": "Services not available"}

    return {
        "message": "Dependency Chain Test",
        "chain": [
            "1. ReportService requested",
            "2. ServiceProvider sees it needs: ILogger, IConfig, ITimeService",
            "3. ILogger resolved (singleton, already created)",
            "4. IConfig resolved (singleton, already created)",
            "5. ITimeService resolved (singleton, already created)",
            "6. ReportService created with all dependencies injected"
        ],
        "result": "All dependencies automatically resolved and injected!",
        "time": time_service.get_current_time()
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Constructor Injection Example Server")
    print("=" * 70)
    print()
    print("Server URL: http://localhost:8093")
    print()
    print("Key Feature: Automatic Dependency Injection via Type Hints")
    print("  - No manual factory functions needed")
    print("  - Dependencies resolved from constructor type hints")
    print("  - Clean, maintainable code")
    print()
    print("Available Endpoints:")
    print("  GET /hello")
    print("  GET /report/:type")
    print("  GET /user/:id")
    print("  GET /injection/info")
    print("  GET /test/dependency-chain")
    print()
    print("Example URLs:")
    print("  - http://localhost:8093/hello")
    print("  - http://localhost:8093/report/daily")
    print("  - http://localhost:8093/user/12345")
    print("  - http://localhost:8093/injection/info")
    print("  - http://localhost:8093/test/dependency-chain")
    print()
    print("=" * 70)
    print()

    app.listening()
