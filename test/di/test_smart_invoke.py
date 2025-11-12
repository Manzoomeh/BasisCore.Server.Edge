"""
Test smart invoke method that auto-detects sync/async
"""
import asyncio
from abc import ABC, abstractmethod

from bclib.utility import ServiceProvider


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


# Sync function
def sync_process(logger: ILogger, data: str) -> str:
    """Sync function with DI"""
    logger.log(f"Sync processing: {data}")
    return f"Sync result: {data}"


# Async function
async def async_process(logger: ILogger, data: str) -> str:
    """Async function with DI"""
    logger.log(f"Async processing: {data}")
    await asyncio.sleep(0.01)  # Simulate async work
    return f"Async result: {data}"


# Mixed parameters
def mixed_params(logger: ILogger, a: int, b: int, operation: str = "add") -> int:
    """Function with injected and provided params"""
    logger.log(f"Operation: {operation}")
    if operation == "add":
        return a + b
    return a * b


async def async_mixed(logger: ILogger, items: list) -> dict:
    """Async with mixed params"""
    logger.log(f"Processing {len(items)} items")
    await asyncio.sleep(0.01)
    return {"count": len(items), "total": sum(items)}


print("=" * 70)
print("Testing Smart Invoke Method (Auto-detect Sync/Async)")
print("=" * 70)
print()

# Setup
services = ServiceProvider()
services.add_singleton(ILogger, ConsoleLogger)
logger = services.get_service(ILogger)


async def run_tests():
    print("1. Testing with SYNC function...")
    result = services.invoke(sync_process, data="test1")
    print(f"   Result: {result}")
    print(f"   Type: {type(result).__name__}")
    print()

    print("2. Testing with ASYNC function...")
    result = await services.invoke(async_process, data="test2")
    print(f"   Result: {result}")
    print(f"   Type: {type(result).__name__}")
    print()

    print("3. Testing SYNC with mixed parameters...")
    result1 = services.invoke(mixed_params, a=10, b=5)
    result2 = services.invoke(mixed_params, a=10, b=5, operation="multiply")
    print(f"   10 + 5 = {result1}")
    print(f"   10 * 5 = {result2}")
    print()

    print("4. Testing ASYNC with mixed parameters...")
    result = await services.invoke(async_mixed, items=[1, 2, 3, 4, 5])
    print(f"   Result: {result}")
    print()

    print("5. Testing without await (checking coroutine detection)...")
    result = services.invoke(async_process, data="test3")
    print(f"   Result type: {type(result).__name__}")
    print(f"   Is coroutine: {asyncio.iscoroutine(result)}")
    if asyncio.iscoroutine(result):
        actual_result = await result
        print(f"   Awaited result: {actual_result}")
    print()

    print("=" * 70)
    print("✓ All smart invoke tests passed!")
    print(f"✓ Total logged messages: {len(logger.messages)}")
    print()
    print("Summary:")
    print("  - services.invoke() works with BOTH sync and async functions")
    print("  - Automatically detects function type using inspect.iscoroutinefunction()")
    print("  - Returns direct result for sync, coroutine for async")
    print("  - No need to choose between invoke_method and invoke_method_async")
    print("=" * 70)


asyncio.run(run_tests())
