"""
Quick test to verify modular service_provider structure
"""
from bclib.service_provider import (InjectionPlan, ServiceDescriptor,
                                    ServiceLifetime, ServiceProvider)

print("=" * 70)
print("Testing Modular Service Provider")
print("=" * 70)

# Test 1: Import all classes
print("\n✓ Test 1: All imports successful")
print(f"  - ServiceProvider: {ServiceProvider}")
print(f"  - ServiceLifetime: {ServiceLifetime}")
print(f"  - ServiceDescriptor: {ServiceDescriptor}")
print(f"  - InjectionPlan: {InjectionPlan}")

# Test 2: Create ServiceProvider instance
services = ServiceProvider()
print("\n✓ Test 2: ServiceProvider instance created")
print(f"  - {services}")

# Test 3: Register services


class ILogger:
    def log(self, message: str):
        pass


class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"[LOG] {message}")


services.add_singleton(ILogger, ConsoleLogger)
print("\n✓ Test 3: Service registered")

# Test 4: Resolve service
logger = services.get_service(ILogger)
print("\n✓ Test 4: Service resolved")
print(f"  - Logger instance: {logger}")

# Test 5: Use service
logger.log("Testing modular service provider")
print("\n✓ Test 5: Service working")

# Test 6: Check service lifetime
lifetime = services.get_lifetime(ILogger)
print("\n✓ Test 6: Service lifetime check")
print(f"  - ILogger lifetime: {lifetime}")

# Test 7: InjectionPlan


def test_handler(logger: ILogger, name: str):
    logger.log(f"Handler called with {name}")
    return f"Hello {name}"


plan = InjectionPlan(test_handler)
print("\n✓ Test 7: InjectionPlan created")
print(f"  - {plan}")
print(f"  - Strategies: {plan.param_strategies}")

print("\n" + "=" * 70)
print("All Tests Passed! ✓")
print("Modular service_provider structure is working correctly")
print("=" * 70)
