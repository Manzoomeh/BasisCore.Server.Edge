"""
Quick test for Constructor Injection
"""
from abc import ABC, abstractmethod

from bclib.utility import ServiceProvider


class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass


class ConsoleLogger(ILogger):
    def __init__(self):
        print("ConsoleLogger created")

    def log(self, message: str):
        print(f"[LOG] {message}")


class IConfig(ABC):
    @abstractmethod
    def get(self, key: str) -> str:
        pass


class SimpleConfig(IConfig):
    def __init__(self):
        print("SimpleConfig created")
        self.data = {"app": "test"}

    def get(self, key: str) -> str:
        return self.data.get(key, "")


class ServiceWithDependencies:
    """Service with constructor injection"""

    def __init__(self, logger: ILogger, config: IConfig):
        print("ServiceWithDependencies created")
        self.logger = logger
        self.config = config


# Test constructor injection
print("=" * 60)
print("Testing Constructor Injection")
print("=" * 60)
print()

services = ServiceProvider()

# Register base services
print("1. Registering base services...")
services.add_singleton(ILogger, ConsoleLogger)
services.add_singleton(IConfig, SimpleConfig)
print()

# Register service with dependencies (no factory needed!)
print("2. Registering ServiceWithDependencies (with auto-injection)...")
services.add_transient(ServiceWithDependencies)
print()

# Resolve service - dependencies should be auto-injected
print("3. Resolving ServiceWithDependencies...")
service = services.get_service(ServiceWithDependencies)
print()

if service:
    print("✓ SUCCESS! Service created with dependencies injected")
    print(f"  - Has logger: {service.logger is not None}")
    print(f"  - Has config: {service.config is not None}")
    print()

    print("4. Testing injected dependencies...")
    service.logger.log("Constructor injection works!")
    app_name = service.config.get("app")
    print(f"  - Config value: {app_name}")
    print()

    print("=" * 60)
    print("✓ All tests passed! Constructor Injection is working!")
    print("=" * 60)
else:
    print("✗ FAILED: Service not created")
