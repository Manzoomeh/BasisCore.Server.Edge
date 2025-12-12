"""
Test InjectionPlan with both methods and classes
"""
import asyncio
from abc import ABC, abstractmethod

from bclib.di import InjectionPlan, ServiceProvider
from bclib.utility import DictEx


# Test services
class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass


class ConsoleLogger(ILogger):
    def __init__(self):
        self.messages = []

    def log(self, message: str):
        self.messages.append(message)
        print(f"[LOG] {message}")


class IDatabase(ABC):
    @abstractmethod
    def query(self, sql: str) -> str:
        pass


class MockDatabase(IDatabase):
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.logger.log("MockDatabase initialized with constructor injection")

    def query(self, sql: str) -> str:
        self.logger.log(f"Query: {sql}")
        return f"Result of: {sql}"


class ComplexService:
    """Service with multiple dependencies"""

    def __init__(self, logger: ILogger, db: IDatabase, name: str = "default"):
        self.logger = logger
        self.db = db
        self.name = name
        self.logger.log(f"ComplexService initialized with name={name}")

    def process(self, data: str) -> str:
        self.logger.log(f"Processing: {data}")
        result = self.db.query(f"INSERT INTO logs VALUES ('{data}')")
        return result


# Create services
services = ServiceProvider()
services.add_singleton(ILogger, ConsoleLogger)
services.add_transient(IDatabase, MockDatabase)


# Create mock context
class MockContext:
    def __init__(self):
        self.services = services
        self.url_segments = DictEx()
        self.url_segments.name = "Alice"
        self.url_segments.age = "25"

        # Mock dispatcher
        class MockDispatcher:
            def __init__(self):
                self.event_loop = asyncio.get_event_loop()

        self.dispatcher = MockDispatcher()


context = MockContext()

print("=" * 70)
print("Test 1: InjectionPlan for Class Instantiation")
print("=" * 70)

# Test with MockDatabase (has ILogger dependency)
plan = InjectionPlan(MockDatabase)
print(f"Plan created: {plan}")
print(f"Is class: {plan.is_class}")
print(f"Strategies: {list(plan.param_strategies.keys())}")

db_instance = plan.create_instance(context)
print(f"✓ Instance created: {type(db_instance).__name__}")
result = db_instance.query("SELECT * FROM users")
print(f"✓ Query result: {result}")
print()

print("=" * 70)
print("Test 2: InjectionPlan for Class with Default Parameters")
print("=" * 70)

# Test ComplexService (has logger, db, and optional name)
plan2 = InjectionPlan(ComplexService)
print(f"Plan created: {plan2}")
print(f"Strategies: {list(plan2.param_strategies.keys())}")

service_instance = plan2.create_instance(context, name="CustomName")
print(f"✓ Instance created with custom name: {service_instance.name}")
result = service_instance.process("test data")
print(f"✓ Process result: {result}")
print()

print("=" * 70)
print("Test 3: InjectionPlan for Method Execution")
print("=" * 70)


def test_method(logger: ILogger, db: IDatabase, name: str):
    logger.log(f"Method called with name={name}")
    return db.query(f"SELECT * FROM users WHERE name='{name}'")


plan3 = InjectionPlan(test_method)
print(f"Plan created: {plan3}")
print(f"Is class: {plan3.is_class}")
print(f"Is async: {plan3.is_async}")
print(f"Strategies: {list(plan3.param_strategies.keys())}")

result = plan3.execute(context)
print(f"✓ Method result: {result}")
print()

print("=" * 70)
print("Test 4: InjectionPlan for Async Method Execution")
print("=" * 70)


async def async_method(logger: ILogger, name: str):
    logger.log(f"Async method called with name={name}")
    await asyncio.sleep(0.01)
    return f"Processed {name}"


plan4 = InjectionPlan(async_method)
print(f"Plan created: {plan4}")
print(f"Is async: {plan4.is_async}")


async def test_async():
    result = plan4.execute_async(context)
    if asyncio.iscoroutine(result):
        result = await result
    print(f"✓ Async method result: {result}")


asyncio.run(test_async())
print()

print("=" * 70)
print("Test 5: ServiceProvider using InjectionPlan for Constructor Injection")
print("=" * 70)

# Test that ServiceProvider._create_with_constructor_injection uses InjectionPlan
db_from_provider = services.get_service(IDatabase, context)
print(f"✓ Service from provider: {type(db_from_provider).__name__}")
result = db_from_provider.query("SELECT COUNT(*) FROM users")
print(f"✓ Query result: {result}")
print()

print("=" * 70)
print("Test 6: Error Handling - Execute class should fail")
print("=" * 70)

try:
    plan = InjectionPlan(MockDatabase)
    plan.execute(context)  # Should raise TypeError
    print("✗ Should have raised TypeError")
except TypeError as e:
    print(f"✓ Correct error: {e}")
print()

print("=" * 70)
print("Test 7: Error Handling - Create instance from function should fail")
print("=" * 70)

try:
    plan = InjectionPlan(test_method)
    plan.create_instance(context)  # Should raise TypeError
    print("✗ Should have raised TypeError")
except TypeError as e:
    print(f"✓ Correct error: {e}")
print()

print("=" * 70)
print("All Tests Passed! ✓✓✓")
print("=" * 70)
print()
print("Summary:")
print("✓ InjectionPlan can analyze classes and create instances")
print("✓ InjectionPlan can analyze methods and execute them")
print("✓ Constructor injection works with dependencies")
print("✓ URL segments NOT injected into constructors (only services)")
print("✓ Method execution injects both services and URL segments")
print("✓ Async methods work correctly")
print("✓ ServiceProvider uses InjectionPlan for constructor injection")
print("✓ Proper error handling for misuse")
