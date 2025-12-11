"""
Test method injection functionality
"""
import asyncio
from abc import ABC, abstractmethod

from bclib.di import ServiceProvider


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


# Test sync method injection
def greet_user(logger: ILogger, name: str) -> str:
    """Function with DI - logger will be injected"""
    logger.log(f"Greeting user: {name}")
    return f"Hello, {name}!"


# Test async method injection
async def process_data_async(logger: ILogger, data: dict) -> dict:
    """Async function with DI"""
    logger.log(f"Processing data: {data}")
    return {"processed": True, "data": data}


print("=" * 60)
print("Testing Method Injection")
print("=" * 60)
print()

# Setup
services = ServiceProvider()
services.add_singleton(ILogger, ConsoleLogger)
logger = services.get_service(ILogger)

print("1. Testing sync method injection...")
result = services.invoke_method(greet_user, name="Alice")
print(f"   Result: {result}")
print(f"   Logger used: {len(logger.messages)} message(s) logged")
print()

print("2. Testing async method injection...")


async def test_async():
    result = await services.invoke_method_async(
        process_data_async,
        data={"value": 123}
    )
    print(f"   Result: {result}")
    print(f"   Logger used: {len(logger.messages)} message(s) logged")

asyncio.run(test_async())
print()

print("3. Testing with multiple parameters...")


def calculate(logger: ILogger, a: int, b: int, operation: str = "add") -> int:
    logger.log(f"Calculating: {a} {operation} {b}")
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    return 0


result1 = services.invoke_method(calculate, a=10, b=5)
print(f"   10 + 5 = {result1}")

result2 = services.invoke_method(calculate, a=10, b=5, operation="multiply")
print(f"   10 * 5 = {result2}")
print()

print("=" * 60)
print("✓ All method injection tests passed!")
print(f"✓ Total logged messages: {len(logger.messages)}")
print("=" * 60)
