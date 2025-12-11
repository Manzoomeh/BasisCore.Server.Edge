"""Test optional context injection"""
import os
import sys

from bclib.context import RESTfulContext
from bclib.di import ServiceProvider

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


# Mock services
class ILogger:
    def log(self, msg: str):
        pass


class ConsoleLogger(ILogger):
    def log(self, msg: str):
        print(f"[LOG] {msg}")


class IDatabase:
    def save(self, data: str):
        pass


class MockDatabase(IDatabase):
    def save(self, data: str):
        print(f"[DB] Saving: {data}")


# Test handlers with different signatures

def handler_with_context_only(context: RESTfulContext):
    """Handler that only needs context"""
    return f"Has context: {context is not None}"


def handler_with_logger_only(logger: ILogger):
    """Handler that only needs logger (no context)"""
    logger.log("Handler called without context!")
    return "Logger only"


def handler_with_both(context: RESTfulContext, logger: ILogger):
    """Handler with both context and logger"""
    logger.log(f"Has context: {context is not None}")
    return "Both injected"


def handler_with_all(context: RESTfulContext, logger: ILogger, db: IDatabase):
    """Handler with context and multiple services"""
    logger.log("All services injected")
    db.save("test data")
    return f"Context: {context is not None}"


def handler_with_no_context(logger: ILogger, db: IDatabase, custom_param: str):
    """Handler without context but with services and custom param"""
    logger.log(f"Custom: {custom_param}")
    db.save(custom_param)
    return "No context needed"


if __name__ == "__main__":
    # Setup DI
    services = ServiceProvider()
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_singleton(IDatabase, MockDatabase)

    # Mock context
    class MockContext(RESTfulContext):
        def __init__(self):
            pass

    context = MockContext()

    print("=" * 60)
    print("Testing Optional Context Injection")
    print("=" * 60)

    # Test 1: Handler with only context
    print("\n1. Handler with context only:")
    injected = services.inject_dependencies(handler_with_context_only, context)
    print(f"   Injected: {injected}")
    result = handler_with_context_only(context, **injected)
    print(f"   Result: {result}")

    # Test 2: Handler without context (only logger)
    print("\n2. Handler with logger only (no context):")
    injected = services.inject_dependencies(handler_with_logger_only, context)
    print(f"   Injected: {list(injected.keys())}")
    result = handler_with_logger_only(**injected)
    print(f"   Result: {result}")

    # Test 3: Handler with both
    print("\n3. Handler with both context and logger:")
    injected = services.inject_dependencies(handler_with_both, context)
    print(f"   Injected: {list(injected.keys())}")
    result = handler_with_both(context, **injected)
    print(f"   Result: {result}")

    # Test 4: Handler with all
    print("\n4. Handler with context and multiple services:")
    injected = services.inject_dependencies(handler_with_all, context)
    print(f"   Injected: {list(injected.keys())}")
    result = handler_with_all(context, **injected)
    print(f"   Result: {result}")

    # Test 5: Handler without context
    print("\n5. Handler without context (services + custom param):")
    injected = services.inject_dependencies(
        handler_with_no_context, context, custom_param="my_value")
    print(f"   Injected: {list(injected.keys())}")
    result = handler_with_no_context(custom_param="my_value", **injected)
    print(f"   Result: {result}")

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
