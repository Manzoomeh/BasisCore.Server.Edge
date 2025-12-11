"""
Example: Using Multiple Implementations in ListenerFactory

This demonstrates how to refactor ListenerFactory to use DI
for managing multiple listener instances instead of manual creation.
"""
from abc import ABC, abstractmethod

from bclib.di import ServiceProvider


# Listener Interface
class IListener(ABC):
    @abstractmethod
    def initialize_task(self, event_loop) -> None:
        """Initialize listener task"""
        pass

    @abstractmethod
    def get_info(self) -> str:
        """Get listener information"""
        pass


# Listener Implementations
class HttpListener(IListener):
    def __init__(self, options: dict):
        self.options = options
        endpoint = options.get('endpoint', 'localhost:8080')
        self.endpoint = endpoint if isinstance(
            endpoint, str) else f"{endpoint.get('url')}:{endpoint.get('port')}"

    def initialize_task(self, event_loop) -> None:
        print(f"HttpListener initialized on {self.endpoint}")

    def get_info(self) -> str:
        return f"HTTP Listener on {self.endpoint}"


class TcpListener(IListener):
    def __init__(self, options: dict):
        self.options = options
        endpoint = options.get('endpoint', 'localhost:3000')
        self.endpoint = endpoint if isinstance(
            endpoint, str) else f"{endpoint.get('url')}:{endpoint.get('port')}"

    def initialize_task(self, event_loop) -> None:
        print(f"TcpListener initialized on {self.endpoint}")

    def get_info(self) -> str:
        return f"TCP Listener on {self.endpoint}"


class RabbitListener(IListener):
    def __init__(self, options: dict):
        self.options = options
        self.queue = options.get('queue', 'default_queue')

    def initialize_task(self, event_loop) -> None:
        print(f"RabbitListener initialized for queue: {self.queue}")

    def get_info(self) -> str:
        return f"RabbitMQ Listener on queue: {self.queue}"


# Listener Factory using DI
class ListenerFactory:
    """
    Factory that receives all registered listeners from DI

    OLD APPROACH:
        - Factory manually creates listener instances
        - Complex normalization logic in factory
        - Hard to test individual listeners

    NEW APPROACH:
        - Listeners registered in DI with their options
        - Factory receives list of all listener instances
        - Clean separation of concerns
    """

    def __init__(self, listeners: list[IListener]):
        """
        Args:
            listeners: All registered listener instances (injected by DI)
        """
        self.listeners = listeners

    def load_listeners(self) -> list[IListener]:
        """Return all listeners"""
        return self.listeners

    def initialize_all(self, event_loop):
        """Initialize all listeners"""
        print(f"\nInitializing {len(self.listeners)} listeners:")
        for listener in self.listeners:
            listener.initialize_task(event_loop)


def example_1_simple_config():
    """Example 1: Simple configuration with single listeners"""
    print("\n" + "="*60)
    print("Example 1: Simple Configuration")
    print("="*60)

    services = ServiceProvider()

    # Register listeners with their options
    services.add_singleton(IListener, factory=lambda sp, **
                           kwargs: HttpListener({"endpoint": "localhost:8080"}))
    services.add_singleton(IListener, factory=lambda sp, **
                           kwargs: TcpListener({"endpoint": "localhost:3000"}))
    services.add_singleton(IListener, factory=lambda sp,
                           **kwargs: RabbitListener({"queue": "tasks"}))

    # Register factory
    services.add_singleton(ListenerFactory)

    # Get factory and use it
    factory = services.get_service(ListenerFactory)
    print(f"\nFactory has {len(factory.listeners)} listeners:")
    for listener in factory.listeners:
        print(f"  - {listener.get_info()}")


def example_2_multiple_http_listeners():
    """Example 2: Multiple HTTP listeners on different ports"""
    print("\n" + "="*60)
    print("Example 2: Multiple HTTP Listeners")
    print("="*60)

    services = ServiceProvider()

    # Register multiple HTTP listeners (simulating array config)
    http_configs = [
        {"endpoint": "localhost:8080"},
        {"endpoint": "localhost:8081"},
        {"endpoint": {"url": "0.0.0.0", "port": 443}}
    ]

    for config in http_configs:
        services.add_singleton(IListener, factory=lambda sp,
                               cfg=config, **kwargs: HttpListener(cfg))

    # Register TCP listener
    services.add_singleton(IListener, factory=lambda sp, **
                           kwargs: TcpListener({"endpoint": "localhost:3000"}))

    # Register factory
    services.add_singleton(ListenerFactory)

    # Get factory
    factory = services.get_service(ListenerFactory)
    print(f"\nFactory has {len(factory.listeners)} listeners:")
    for listener in factory.listeners:
        print(f"  - {listener.get_info()}")


def example_3_with_options_from_config():
    """Example 3: Reading from application options"""
    print("\n" + "="*60)
    print("Example 3: Configuration from AppOptions")
    print("="*60)

    # Simulated app options
    app_options = {
        "http": [
            "localhost:8080",
            {"url": "0.0.0.0", "port": 443}
        ],
        "tcp": "localhost:3000",
        "rabbit": {"queue": "tasks"}
    }

    services = ServiceProvider()

    # Register app options as singleton
    services.add_singleton(dict, instance=app_options)

    # Register listeners based on options
    # HTTP listeners
    http_config = app_options.get('http', [])
    if isinstance(http_config, list):
        for item in http_config:
            config = {"endpoint": item} if isinstance(item, str) else item
            services.add_singleton(
                IListener, factory=lambda sp, cfg=config, **kwargs: HttpListener(cfg))
    else:
        config = {"endpoint": http_config}
        services.add_singleton(IListener, factory=lambda sp,
                               cfg=config, **kwargs: HttpListener(cfg))

    # TCP listener
    if "tcp" in app_options:
        tcp_config = {"endpoint": app_options["tcp"]}
        services.add_singleton(IListener, factory=lambda sp,
                               cfg=tcp_config, **kwargs: TcpListener(cfg))

    # RabbitMQ listener
    if "rabbit" in app_options:
        rabbit_config = app_options["rabbit"]
        services.add_singleton(IListener, factory=lambda sp,
                               cfg=rabbit_config, **kwargs: RabbitListener(cfg))

    # Register factory
    services.add_singleton(ListenerFactory)

    # Get factory
    factory = services.get_service(ListenerFactory)
    print(f"\nFactory has {len(factory.listeners)} listeners:")
    for listener in factory.listeners:
        print(f"  - {listener.get_info()}")


def example_4_testing_individual_listeners():
    """Example 4: Easy testing of individual listeners"""
    print("\n" + "="*60)
    print("Example 4: Testing Individual Listeners")
    print("="*60)

    services = ServiceProvider()

    # Register only HTTP listener for testing
    services.add_singleton(IListener, factory=lambda sp, **
                           kwargs: HttpListener({"endpoint": "localhost:8080"}))

    # Get single listener (first one)
    listener = services.get_service(IListener)
    print(f"\nTesting single listener: {listener.get_info()}")

    # Or get all listeners (returns list with one item)
    all_listeners = services.get_service(list[IListener])
    print(f"All listeners: {len(all_listeners)} item(s)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ListenerFactory with Multiple DI Implementations")
    print("="*60)

    example_1_simple_config()
    example_2_multiple_http_listeners()
    example_3_with_options_from_config()
    example_4_testing_individual_listeners()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)
