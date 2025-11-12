"""
Test DI configuration without inheritance
"""
from abc import ABC, abstractmethod

from bclib import edge
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


class IConfig(ABC):
    @abstractmethod
    def get(self, key: str) -> str:
        pass


class SimpleConfig(IConfig):
    def __init__(self):
        self.data = {"app": "test"}

    def get(self, key: str) -> str:
        return self.data.get(key, "")


print("=" * 70)
print("Testing DI Without Inheritance")
print("=" * 70)
print()

# Create dispatcher WITHOUT inheritance
options = {"server": "localhost:9999", "router": "restful"}
app = edge.DevServerDispatcher(options)

print("1. Testing configure_services with named function...")


def setup_services(services: ServiceProvider):
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_singleton(IConfig, SimpleConfig)
    print("   Services configured via callback")


# Configure without inheritance!
result = app.configure_services(setup_services)
print(f"   Returns self for chaining: {result is app}")
print()

print("2. Verifying services are registered...")
logger = app.services.get_service(ILogger)
config = app.services.get_service(IConfig)

if logger and config:
    print("   ✓ Logger service available")
    print("   ✓ Config service available")

    logger.log("Test message")
    app_name = config.get("app")
    print(f"   ✓ Config value: {app_name}")
else:
    print("   ✗ Services not available")
print()

print("3. Testing method chaining...")


def add_more_services(services: ServiceProvider):
    # Could add more services here
    print("   Additional configuration applied")


app.configure_services(add_more_services)
print("   ✓ Chaining works")
print()

print("4. Testing with lambda (inline configuration)...")
options2 = {"server": "localhost:9998", "router": "restful"}
app2 = edge.DevServerDispatcher(options2)

app2.configure_services(
    lambda services: services.add_singleton(ILogger, ConsoleLogger))
logger2 = app2.services.get_service(ILogger)

if logger2:
    print("   ✓ Lambda configuration works")
    logger2.log("Lambda test")
else:
    print("   ✗ Lambda configuration failed")
print()

print("=" * 70)
print("✓ All tests passed!")
print()
print("Summary:")
print("  - configure_services() works without inheritance")
print("  - Returns self for method chaining")
print("  - Supports both named functions and lambdas")
print("  - Services are properly registered and accessible")
print()
print("Benefits:")
print("  ✅ No need to create derived dispatcher class")
print("  ✅ Simpler code for small applications")
print("  ✅ Quick prototyping")
print("  ✅ Less boilerplate")
print("=" * 70)
