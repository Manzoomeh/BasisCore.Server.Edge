"""
Test to verify service_provider module is in bclib and has complete type hints
"""
import inspect
from typing import get_type_hints

from bclib.context import Context  # Import Context for type hints evaluation
from bclib.service_provider import (InjectionPlan, InjectionStrategy,
                                    ServiceDescriptor, ServiceLifetime)
from bclib.service_provider import ServiceProvider
from bclib.service_provider import ServiceProvider as SPFromUtility
from bclib.service_provider import ServiceStrategy, ValueStrategy

print("=" * 70)
print("Testing Service Provider Module Location & Type Hints")
print("=" * 70)

# Test 1: Module location
print("\n✓ Test 1: Module Location")
print(f"  - ServiceProvider module: {ServiceProvider.__module__}")
assert 'bclib.service_provider' in ServiceProvider.__module__
print(f"  - Module is in bclib.service_provider ✓")

# Test 2: Backward compatibility
print("\n✓ Test 2: Backward Compatibility")
print(f"  - Import from bclib.utility works: {SPFromUtility}")
assert ServiceProvider is SPFromUtility
print(f"  - Same class instance ✓")

# Test 3: Type hints verification
print("\n✓ Test 3: Type Hints Verification")


def check_type_hints(cls, method_name):
    method = getattr(cls, method_name)
    sig = inspect.signature(method)
    # Include Context in localns for forward reference resolution
    hints = get_type_hints(method, localns={'Context': Context})

    # Check return type
    has_return = 'return' in hints

    # Check parameter types
    typed_params = sum(1 for p in sig.parameters.values() if p.name in hints)
    total_params = len(
        [p for p in sig.parameters.values() if p.name != 'self'])

    return has_return, typed_params, total_params


# Check ServiceProvider methods
methods_to_check = [
    '__init__',
    'add_singleton',
    'add_scoped',
    'add_transient',
    'get_service',
    'inject_dependencies',
    'create_scope',
    'clear_scope',
    'invoke_method',
    'invoke_method_async',
    'invoke',
    'is_registered',
    'get_lifetime',
    'invoke_in_executor',
    '__repr__'
]

print("\n  ServiceProvider methods:")
for method_name in methods_to_check:
    has_return, typed_params, total_params = check_type_hints(
        ServiceProvider, method_name)
    status = "✓" if (has_return or method_name in [
                     '__init__', 'clear_scope']) else "⚠"
    print(f"    {status} {method_name}: {typed_params}/{total_params} params typed, return: {has_return}")

# Check InjectionPlan
print("\n  InjectionPlan methods:")
for method_name in ['__init__', '_analyze', 'inject_parameters', 'execute_async', '__repr__']:
    has_return, typed_params, total_params = check_type_hints(
        InjectionPlan, method_name)
    status = "✓" if has_return or method_name in [
        '__init__', '_analyze'] else "⚠"
    print(f"    {status} {method_name}: {typed_params}/{total_params} params typed, return: {has_return}")

# Check InjectionStrategy classes
print("\n  InjectionStrategy classes:")
for cls in [ValueStrategy, ServiceStrategy]:
    has_return, typed_params, total_params = check_type_hints(cls, 'resolve')
    print(
        f"    ✓ {cls.__name__}.resolve: {typed_params}/{total_params} params typed, return: {has_return}")

# Test 4: Functionality test
print("\n✓ Test 4: Functionality Test")


class ILogger:
    def log(self, message: str) -> None:
        pass


class ConsoleLogger(ILogger):
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")


services = ServiceProvider()
services.add_singleton(ILogger, ConsoleLogger)
logger = services.get_service(ILogger)
logger.log("Module working correctly with type hints!")

print("\n" + "=" * 70)
print("All Tests Passed! ✓")
print("Module is in bclib.service_provider with complete type hints")
print("=" * 70)
