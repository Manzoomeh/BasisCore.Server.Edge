"""
Method Injection Example

Demonstrates automatic dependency injection for method calls.
Type-hinted parameters are automatically resolved from DI container.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from bclib import edge
from bclib.context import RESTfulContext
from bclib.service_provider import ServiceProvider

# ==================== Services ====================


class ILogger(ABC):
    @abstractmethod
    def log(self, message: str, level: str = "INFO"):
        pass


class IDatabase(ABC):
    @abstractmethod
    async def query(self, sql: str) -> list:
        pass

    @abstractmethod
    async def save(self, data: dict) -> bool:
        pass


class IEmailService(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        pass


# ==================== Implementations ====================

class ConsoleLogger(ILogger):
    def __init__(self):
        self.log_count = 0

    def log(self, message: str, level: str = "INFO"):
        self.log_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")


class MockDatabase(IDatabase):
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.data = []
        self.logger.log("MockDatabase initialized")

    async def query(self, sql: str) -> list:
        self.logger.log(f"Executing query: {sql}", "DEBUG")
        return self.data

    async def save(self, data: dict) -> bool:
        self.logger.log(f"Saving data: {data}", "DEBUG")
        self.data.append(data)
        return True


class MockEmailService(IEmailService):
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.sent_emails = []
        self.logger.log("MockEmailService initialized")

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        self.logger.log(f"Sending email to {to}: {subject}", "INFO")
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True


# ==================== Business Logic Functions ====================

def calculate_total(logger: ILogger, items: list) -> float:
    """
    Calculate total - logger automatically injected

    Notice: No need to pass logger manually!
    """
    logger.log(f"Calculating total for {len(items)} items")
    total = sum(item.get("price", 0) for item in items)
    logger.log(f"Total calculated: {total}")
    return total


async def process_order(
    logger: ILogger,           # Injected from DI
    db: IDatabase,             # Injected from DI
    email: IEmailService,      # Injected from DI
    order_data: dict           # Must be provided by caller
):
    """
    Process order with multiple injected dependencies

    logger, db, and email are automatically injected.
    Only order_data needs to be provided by caller.
    """
    logger.log(f"Processing order: {order_data.get('order_id')}")

    # Save to database
    await db.save(order_data)

    # Send confirmation email
    customer_email = order_data.get("customer_email", "customer@example.com")
    await email.send_email(
        to=customer_email,
        subject="Order Confirmation",
        body=f"Your order {order_data.get('order_id')} has been processed."
    )

    logger.log("Order processed successfully")
    return {"status": "success", "order_id": order_data.get("order_id")}


def validate_data(
    logger: ILogger,
    data: dict,
    required_fields: list = None
) -> tuple[bool, str]:
    """
    Validate data with optional parameters

    logger is injected, data and required_fields are provided by caller.
    """
    logger.log("Validating data...")

    if required_fields is None:
        required_fields = ["name", "email"]

    for field in required_fields:
        if field not in data:
            logger.log(f"Validation failed: missing {field}", "ERROR")
            return False, f"Missing required field: {field}"

    logger.log("Validation passed")
    return True, "Valid"


async def generate_report(
    db: IDatabase,
    logger: ILogger,
    report_type: str,
    filters: Optional[dict] = None
) -> dict:
    """
    Generate report with mixed injected and provided parameters
    """
    logger.log(f"Generating {report_type} report...")

    # Query data
    data = await db.query(f"SELECT * FROM {report_type}")

    # Apply filters if provided
    if filters:
        logger.log(f"Applying filters: {filters}")

    logger.log(f"Report generated with {len(data)} records")

    return {
        "type": report_type,
        "records": len(data),
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


# ==================== Dispatcher ====================

class MethodInjectionDispatcher(edge.DevServerDispatcher):
    def __init__(self, options):
        super().__init__(options)

        print("\n" + "=" * 70)
        print("Configuring Method Injection Services")
        print("=" * 70)

        self.add_singleton(ILogger, ConsoleLogger)
        self.add_scoped(IDatabase, MockDatabase)
        self.add_transient(IEmailService, MockEmailService)

        print("✓ Services registered")
        print("=" * 70 + "\n")


options = {"server": "localhost:8094", "router": "restful"}
app = MethodInjectionDispatcher(options)


# ==================== Handlers ====================

@app.restful_handler()
async def calculate(context: RESTfulContext):
    """
    Calculate total using method injection

    GET http://localhost:8094/calculate
    POST http://localhost:8094/calculate
    Body: {"items": [{"price": 10}, {"price": 20}]}
    """
    items = context.parameter("items", [
        {"price": 10},
        {"price": 20},
        {"price": 30}
    ])

    # Using smart invoke - automatically detects sync function
    total = context.services.invoke(calculate_total, items=items)

    return {
        "items": items,
        "total": total,
        "note": "Smart invoke detected sync function and injected logger automatically"
    }


@app.restful_handler("/order")
async def create_order(context: RESTfulContext):
    """
    Create order using async method injection

    POST http://localhost:8094/order
    Body: {
        "order_id": "ORD-001",
        "customer_email": "customer@example.com",
        "items": [{"product": "Widget", "price": 99.99}]
    }
    """
    order_data = {
        "order_id": context.parameter("order_id", "ORD-001"),
        "customer_email": context.parameter("customer_email", "customer@example.com"),
        "items": context.parameter("items", []),
        "timestamp": datetime.now().isoformat()
    }

    # Using smart invoke - automatically detects async function!
    result = await context.services.invoke(
        process_order,
        order_data=order_data
    )

    return {
        "result": result,
        "note": "Smart invoke detected async function and injected 3 dependencies automatically"
    }


@app.restful_handler("/validate")
async def validate(context: RESTfulContext):
    """
    Validate data using method injection

    POST http://localhost:8094/validate
    Body: {
        "data": {"name": "John", "email": "john@example.com"},
        "required_fields": ["name", "email", "phone"]
    }
    """
    data = context.parameter(
        "data", {"name": "John", "email": "john@example.com"})
    required_fields = context.parameter("required_fields", None)

    # Using smart invoke - works for sync functions
    is_valid, message = context.services.invoke(
        validate_data,
        data=data,
        required_fields=required_fields
    )

    return {
        "valid": is_valid,
        "message": message,
        "data": data,
        "note": "Smart invoke auto-detected sync function and injected logger"
    }


@app.restful_handler("/report/:type")
async def report(context: RESTfulContext):
    """
    Generate report using method injection

    GET http://localhost:8094/report/sales
    GET http://localhost:8094/report/users
    """
    report_type = context.url_segments.type
    filters = context.parameter("filters", None)

    # Using smart invoke - automatically detects async function
    report_data = await context.services.invoke(
        generate_report,
        report_type=report_type,
        filters=filters
    )

    return {
        "report": report_data,
        "note": "Smart invoke detected async function and injected db and logger"
    }


@app.restful_handler("/method-injection/info")
async def info(context: RESTfulContext):
    """
    Information about method injection

    GET http://localhost:8094/method-injection/info
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Showing method injection info")

    return {
        "title": "Method Injection with Type Hints",
        "description": "Call any function with automatic dependency injection",
        "features": [
            "Automatic parameter resolution from type hints",
            "Support for sync and async methods",
            "Explicit arguments override DI resolution",
            "Works with optional parameters"
        ],
        "methods": {
            "invoke()": "⭐ Smart invoke - auto-detects sync/async (RECOMMENDED)",
            "invoke_method()": "For synchronous functions only",
            "invoke_method_async()": "For asynchronous functions only"
        },
        "example_smart": {
            "code": "await services.invoke(any_function, param='value')",
            "description": "⭐ Works for both sync and async - auto-detection!"
        },
        "example_sync": {
            "code": "services.invoke_method(my_function, custom_param='value')",
            "description": "Type-hinted params injected, custom_param provided"
        },
        "example_async": {
            "code": "await services.invoke_method_async(async_function, data=data)",
            "description": "Async function with DI support"
        },
        "benefits": [
            "Keep business logic functions pure (no DI coupling)",
            "Easy to test (can call functions directly with mocks)",
            "Flexible - mix injected and provided parameters",
            "Works with existing functions (no modification needed)"
        ],
        "use_cases": [
            "Business logic functions that need services",
            "Handlers that want to delegate to pure functions",
            "Testing scenarios with mock services",
            "Legacy code integration"
        ]
    }


@app.restful_handler("/test/complex")
async def test_complex(context: RESTfulContext):
    """
    Test complex method injection scenario

    GET http://localhost:8094/test/complex
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Testing complex method injection...")

    # Define inline function with DI
    def process_items(logger: ILogger, items: list, multiplier: float = 1.0) -> dict:
        logger.log(
            f"Processing {len(items)} items with multiplier {multiplier}")
        total = sum(item.get("value", 0) for item in items) * multiplier
        return {"total": total, "count": len(items)}

    items = [{"value": 10}, {"value": 20}, {"value": 30}]

    # Test with default multiplier using smart invoke
    result1 = context.services.invoke(process_items, items=items)

    # Test with custom multiplier
    result2 = context.services.invoke(
        process_items, items=items, multiplier=2.0)

    return {
        "test": "Complex Method Injection",
        "result_default": result1,
        "result_custom": result2,
        "note": "Smart invoke detected sync function and injected logger"
    }


@app.restful_handler("/smart-invoke/demo")
async def smart_invoke_demo(context: RESTfulContext):
    """
    Demonstrate smart invoke with both sync and async functions

    GET http://localhost:8094/smart-invoke/demo
    """
    logger = context.get_service(ILogger)
    if logger:
        logger.log("Testing smart invoke with mixed functions...")

    # Define sync function
    def sync_calc(logger: ILogger, a: int, b: int) -> int:
        logger.log(f"Sync: {a} + {b}")
        return a + b

    # Define async function
    async def async_calc(logger: ILogger, a: int, b: int) -> int:
        logger.log(f"Async: {a} * {b}")
        return a * b

    # Smart invoke handles both automatically!
    sync_result = context.services.invoke(sync_calc, a=10, b=5)
    async_result = await context.services.invoke(async_calc, a=10, b=5)

    return {
        "title": "Smart Invoke Demo",
        "sync_result": {
            "function": "sync_calc",
            "operation": "10 + 5",
            "result": sync_result,
            "method_used": "Detected sync, called invoke_method()"
        },
        "async_result": {
            "function": "async_calc",
            "operation": "10 * 5",
            "result": async_result,
            "method_used": "Detected async, called invoke_method_async()"
        },
        "benefit": "One method (invoke) works for both sync and async functions!",
        "usage": "result = await services.invoke(any_function, params...)"
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Method Injection Example Server")
    print("=" * 70)
    print()
    print("Server URL: http://localhost:8094")
    print()
    print("Key Feature: Automatic Dependency Injection for Method Calls")
    print("  - Call any function with services.invoke_method()")
    print("  - Type-hinted parameters automatically resolved")
    print("  - Support for both sync and async methods")
    print()
    print("Available Endpoints:")
    print("  GET  /calculate")
    print("  POST /order")
    print("  POST /validate")
    print("  GET  /report/:type")
    print("  GET  /method-injection/info")
    print("  GET  /test/complex")
    print("  GET  /smart-invoke/demo ⭐")
    print()
    print("Example URLs:")
    print("  - http://localhost:8094/calculate")
    print("  - http://localhost:8094/order")
    print("  - http://localhost:8094/validate")
    print("  - http://localhost:8094/report/sales")
    print("  - http://localhost:8094/method-injection/info")
    print("  - http://localhost:8094/test/complex")
    print("  - http://localhost:8094/smart-invoke/demo ⭐")
    print()
    print("=" * 70)
    print()

    app.listening()
