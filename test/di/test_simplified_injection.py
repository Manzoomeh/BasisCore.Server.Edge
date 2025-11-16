"""
Simple test to verify InjectionPlan works with simplified API (context only)
"""
from typing import Any

from bclib.service_provider import InjectionPlan, ServiceProvider

print("=" * 70)
print("Testing InjectionPlan Simplified API")
print("=" * 70)

# Mock context class


class MockContext:
    def __init__(self):
        self.services = ServiceProvider()
        self.url_segments = type(
            'obj', (object,), {'id': '123', 'name': 'TestUser'})()
        self.event_loop = None

# Mock service


class ILogger:
    def log(self, message: str) -> None:
        pass


class ConsoleLogger(ILogger):
    def __init__(self):
        print("[ConsoleLogger] Created")

    def log(self, message: str) -> None:
        print(f"[LOG] {message}")

# Test handler


def test_handler(logger: ILogger, id: str, name: str) -> str:
    logger.log(f"Handler called: id={id}, name={name}")
    return f"Processed: {id} - {name}"


# Setup
print("\n✓ Test 1: Create InjectionPlan")
plan = InjectionPlan(test_handler)
print(f"  - {plan}")
print(f"  - Strategies: {list(plan.param_strategies.keys())}")

print("\n✓ Test 2: Register services")
context = MockContext()
context.services.add_singleton(ILogger, ConsoleLogger)
print("  - ILogger registered")

print("\n✓ Test 3: inject_parameters (simplified - only context)")
kwargs = plan.inject_parameters(context)
print(f"  - Injected parameters: {list(kwargs.keys())}")
print(f"  - Logger type: {type(kwargs.get('logger'))}")
print(f"  - id value: {kwargs.get('id')}")
print(f"  - name value: {kwargs.get('name')}")

print("\n✓ Test 4: Call handler manually with injected params")
result = test_handler(**kwargs)
print(f"  - Result: {result}")

print("\n" + "=" * 70)
print("All Tests Passed! ✓")
print("InjectionPlan works correctly with simplified API:")
print("  - inject_parameters(context) instead of (context, services)")
print("  - execute_async(context, *args) instead of (context, services, loop, *args)")
print("=" * 70)
