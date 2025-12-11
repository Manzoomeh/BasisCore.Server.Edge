"""
Test Multiple Implementations per Interface in DI Container

Demonstrates how to register and resolve multiple implementations
for a single interface using the ServiceProvider.
"""
from abc import ABC, abstractmethod

from bclib.di import ServiceProvider


# Define interface
class INotificationService(ABC):
    @abstractmethod
    def send(self, message: str) -> str:
        pass


# Define multiple implementations
class EmailNotificationService(INotificationService):
    def send(self, message: str) -> str:
        return f"Email: {message}"


class SmsNotificationService(INotificationService):
    def send(self, message: str) -> str:
        return f"SMS: {message}"


class PushNotificationService(INotificationService):
    def send(self, message: str) -> str:
        return f"Push: {message}"


# Example 1: Register multiple implementations
def test_multiple_implementations():
    print("\n=== Example 1: Multiple Implementations ===")

    services = ServiceProvider()

    # Register three implementations for INotificationService
    services.add_singleton(INotificationService, EmailNotificationService)
    services.add_singleton(INotificationService, SmsNotificationService)
    services.add_singleton(INotificationService, PushNotificationService)

    # Get first implementation (default behavior)
    first_service = services.get_service(INotificationService)
    print(f"First service: {type(first_service).__name__}")
    print(f"Result: {first_service.send('Hello!')}")

    # Get all implementations
    all_services = services.get_service(list[INotificationService])
    print(f"\nAll services count: {len(all_services)}")
    for i, service in enumerate(all_services, 1):
        print(f"{i}. {type(service).__name__}: {service.send('Hello!')}")


# Example 2: Using with dependency injection
class NotificationManager:
    def __init__(self, services: list[INotificationService]):
        self.services = services

    def broadcast(self, message: str):
        results = []
        for service in self.services:
            results.append(service.send(message))
        return results


def test_with_dependency_injection():
    print("\n=== Example 2: Dependency Injection with Multiple Services ===")

    services = ServiceProvider()

    # Register notification services
    services.add_singleton(INotificationService, EmailNotificationService)
    services.add_singleton(INotificationService, SmsNotificationService)
    services.add_singleton(INotificationService, PushNotificationService)

    # Register manager (will auto-inject list of all INotificationService)
    services.add_singleton(NotificationManager)

    # Get manager - it will receive all notification services
    manager = services.get_service(NotificationManager)
    results = manager.broadcast("Important message!")

    print("Broadcast results:")
    for result in results:
        print(f"  - {result}")


# Example 3: Mixed lifetimes
def test_mixed_lifetimes():
    print("\n=== Example 3: Mixed Lifetimes ===")

    services = ServiceProvider()

    # Mix different lifetimes
    services.add_singleton(INotificationService, EmailNotificationService)
    services.add_transient(INotificationService, SmsNotificationService)
    services.add_scoped(INotificationService, PushNotificationService)

    # Get all - each respects its lifetime
    all_services_1 = services.get_service(list[INotificationService])
    all_services_2 = services.get_service(list[INotificationService])

    print(f"First call: {len(all_services_1)} services")
    print(f"Second call: {len(all_services_2)} services")

    # Singleton: same instance
    print(
        f"\nEmail (Singleton) - Same instance: {all_services_1[0] is all_services_2[0]}")

    # Transient: different instance
    print(
        f"SMS (Transient) - Different instance: {all_services_1[1] is all_services_2[1]}")

    # Scoped: same instance in same scope
    print(
        f"Push (Scoped) - Same instance: {all_services_1[2] is all_services_2[2]}")


# Example 4: Practical use case - Listener Factory
class IListener(ABC):
    @abstractmethod
    def start(self) -> str:
        pass


class HttpListener(IListener):
    def start(self) -> str:
        return "HTTP Listener started on port 8080"


class TcpListener(IListener):
    def start(self) -> str:
        return "TCP Listener started on port 3000"


class RabbitListener(IListener):
    def start(self) -> str:
        return "RabbitMQ Listener started"


class ListenerFactory:
    def __init__(self, listeners: list[IListener]):
        self.listeners = listeners

    def start_all(self):
        print("Starting all listeners:")
        for listener in self.listeners:
            print(f"  - {listener.start()}")


def test_listener_factory():
    print("\n=== Example 4: Listener Factory (Practical Use Case) ===")

    services = ServiceProvider()

    # Register multiple listeners
    services.add_singleton(IListener, HttpListener)
    services.add_singleton(IListener, TcpListener)
    services.add_singleton(IListener, RabbitListener)

    # Register factory
    services.add_singleton(ListenerFactory)

    # Get factory and start all listeners
    factory = services.get_service(ListenerFactory)
    factory.start_all()


# Example 5: Using factories
def test_with_factories():
    print("\n=== Example 5: Using Factories ===")

    services = ServiceProvider()

    # Register with factories
    services.add_singleton(
        INotificationService,
        factory=lambda sp, **kwargs: EmailNotificationService()
    )
    services.add_singleton(
        INotificationService,
        factory=lambda sp, **kwargs: SmsNotificationService()
    )

    # Get all services
    all_services = services.get_service(list[INotificationService])
    print(f"Created {len(all_services)} services using factories")
    for service in all_services:
        print(f"  - {type(service).__name__}")


if __name__ == "__main__":
    print("=" * 60)
    print("Multiple Implementations per Interface - Examples")
    print("=" * 60)

    test_multiple_implementations()
    test_with_dependency_injection()
    test_mixed_lifetimes()
    test_listener_factory()
    test_with_factories()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
