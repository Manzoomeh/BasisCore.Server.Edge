"""Simple test of optional context in handlers"""
import os
import sys

from bclib.context import RESTfulContext
from bclib.dispatcher.dispatcher import Dispatcher
from bclib.service_provider import ServiceProvider

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


# Mock services
class ILogger:
    def log(self, msg: str):
        pass


class ConsoleLogger(ILogger):
    def log(self, msg: str):
        print(f"[LOG] {msg}")


# Create a simple test dispatcher
class TestDispatcher(Dispatcher):
    pass


# Create instance
disp = TestDispatcher()

# Setup DI
disp._TestDispatcher__service_provider = ServiceProvider()
disp._TestDispatcher__service_provider.add_singleton(ILogger, ConsoleLogger)


# Test handlers
@disp.restful_handler()
def with_context(context: RESTfulContext):
    """Has context parameter"""
    return {"result": "with_context", "has_context": True}


@disp.restful_handler()
def no_context(logger: ILogger):
    """No context parameter - only logger"""
    logger.log("Handler called without context!")
    return {"result": "no_context", "injected": "logger"}


@disp.restful_handler()
def with_both(context: RESTfulContext, logger: ILogger):
    """Both context and logger"""
    logger.log("Handler with both!")
    return {"result": "with_both", "has_context": True}


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Optional Context Injection in Decorators")
    print("=" * 60)

    # Create mock context
    class MockRESTfulContext(RESTfulContext):
        def __init__(self):
            self.services = disp._TestDispatcher__service_provider

        def generate_response(self, data):
            return data

    context = MockRESTfulContext()

    # Test each handler
    import asyncio

    async def test():
        print("\n1. Handler WITH context parameter:")
        result = await disp.dispatch_async(context)
        print(f"   Would call: with_context(context)")

        print("\n2. Handler WITHOUT context parameter (only logger):")
        print(f"   Would call: no_context(logger)  # context not in signature!")

        print("\n3. Handler with BOTH context and logger:")
        print(f"   Would call: with_both(context, logger)")

    print("\n✅ Handlers registered successfully!")
    print("   - with_context: takes context")
    print("   - no_context: takes only logger (no context!)")
    print("   - with_both: takes context + logger")
    print("\nNote: Actual dispatch test would require full RESTful context")
    print("=" * 60)
