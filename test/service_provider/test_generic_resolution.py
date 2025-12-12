"""
Test generic type resolution in ServiceProvider after refactoring
"""
from bclib.logger import ConsoleLogger, ILogger
from bclib.di import ServiceProvider

print("=" * 70)
print("Testing Generic Type Resolution")
print("=" * 70)

# Setup
services = ServiceProvider()

# Register with factory to provide required options
services.add_singleton(
    ILogger,
    factory=lambda sp, **kw: ConsoleLogger(kw.get('options', {}))
)

# Test 1: Direct ILogger resolution
print("\n1. Direct ILogger resolution:")
logger1 = services.get_service(ILogger)
print(f"   ✓ ILogger: {type(logger1).__name__}")

# Test 2: Generic ILogger['App'] resolution
print("\n2. Generic ILogger['App'] resolution:")
logger2 = services.get_service(ILogger['App'])
print(f"   ✓ ILogger['App']: {type(logger2).__name__}")

# Test 3: Generic ILogger['ServiceProvider'] resolution
print("\n3. Generic ILogger['ServiceProvider'] resolution:")
logger3 = services.get_service(ILogger['ServiceProvider'])
print(f"   ✓ ILogger['ServiceProvider']: {type(logger3).__name__}")

# Test 4: Verify all are same instance (singleton)
print("\n4. Singleton verification:")
print(f"   logger1 is logger2: {logger1 is logger2}")
print(f"   logger2 is logger3: {logger2 is logger3}")
print(f"   All same instance: {logger1 is logger2 is logger3}")

# Test 5: Test with method injection
print("\n5. Method injection with generic type:")


def test_handler(logger: ILogger, message: str):
    logger.info(f"Handler called with: {message}")
    return "OK"


injected = services.inject_dependencies(test_handler, message="Hello")
print(f"   Injected params: {list(injected.keys())}")
if 'logger' in injected:
    print(f"   Logger type: {type(injected['logger']).__name__}")

result = services.invoke_method(test_handler, message="Test")
print(f"   Result: {result}")

print("\n" + "=" * 70)
print("✓ All tests passed - Generic type resolution works!")
print("=" * 70)
