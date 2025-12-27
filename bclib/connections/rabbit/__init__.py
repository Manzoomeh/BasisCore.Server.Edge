"""RabbitMQ Connection Module

Provides modern RabbitMQ connection management inspired by ILogger<T> pattern.
No inheritance required - use IRabbitConnection[TConfig] directly in your services.

Features:
    - Support for both Queue and Exchange modes
    - Lazy connection initialization
    - Type-safe configuration through generics
    - No inheritance required
    - Easy integration with handlers and services

Example:
    ```python
    from bclib.connections.rabbit import IRabbitConnection, add_rabbitmq_connection
    
    # Register RabbitMQ connections
    add_rabbitmq_connection(services)
    
    # Use in service (Queue mode)
    class TaskService:
        def __init__(self, rabbit: IRabbitConnection['rabbitmq.tasks']):
            self.rabbit = rabbit
        
        def queue_task(self, task_data: dict):
            self.rabbit.publish_to_queue(task_data)
    
    # Use in service (Exchange mode)
    class EventService:
        def __init__(self, rabbit: IRabbitConnection['rabbitmq.events']):
            self.rabbit = rabbit
        
        def publish_event(self, event_type: str, data: dict):
            message = {'type': event_type, 'data': data}
            self.rabbit.publish(message, routing_key=f'events.{event_type}')
    ```
"""
from bclib.di import IServiceContainer

from .irabbit_connection import IRabbitConnection

__all__ = ['IRabbitConnection', 'add_rabbitmq_connection']


def add_rabbitmq_connection(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register RabbitMQ Connection Services in DI Container

    Adds RabbitConnection as the implementation for IRabbitConnection[T] in the service provider.
    This allows you to inject IRabbitConnection[TConfig] directly into your services without
    creating custom connection classes.

    Similar to add_logging for ILogger<T>, this function enables the ILogger-style pattern
    for RabbitMQ connections. Supports both Queue and Exchange modes.

    Args:
        service_container: The service container to register services with

    Returns:
        IServiceContainer: The service container for method chaining

    Example:
        ```python
        from bclib.connections.rabbit import add_rabbitmq_connection
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register RabbitMQ connection services
        add_rabbitmq_connection(services)

        # Use in queue mode
        class TaskProcessor:
            def __init__(self, rabbit: IRabbitConnection['rabbitmq.tasks']):
                self.rabbit = rabbit

            def queue_task(self, task_data: dict):
                self.rabbit.publish_to_queue(task_data)

        # Use in exchange mode
        class NotificationService:
            def __init__(self, rabbit: IRabbitConnection['rabbitmq.notifications']):
                self.rabbit = rabbit

            def send_notification(self, user_id: str, message: str):
                notification = {
                    'user_id': user_id,
                    'message': message
                }
                self.rabbit.publish(notification, routing_key='user.notification')

        # Configuration in appsettings.json:
        {
            "rabbitmq": {
                "tasks": {
                    "url": "amqp://guest:guest@localhost:5672/",
                    "queue": "task_queue",
                    "durable": true
                },
                "notifications": {
                    "url": "amqp://guest:guest@localhost:5672/",
                    "exchange": "notifications",
                    "exchange_type": "topic",
                    "routing_key": "user.notification",
                    "durable": true
                }
            }
        }
        ```

    Note:
        After calling this function, you can inject IRabbitConnection['your.config.key']
        into any service constructor. The DI container will automatically:
        1. Resolve configuration from 'your.config.key' 
        2. Create RabbitConnection instance with those options
        3. Provide connection to RabbitMQ with configured queue/exchange
        4. Inject it as IRabbitConnection['your.config.key']
    """
    from bclib.di import IServiceProvider
    from bclib.options import IOptions

    # return service_container.add_transient(IRabbitConnection, RabbitConnection)

    def create_rabbit_connection(service_provider: IServiceProvider, **kwargs):
        """Factory for creating RabbitConnection with configuration key from generic type"""
        from bclib.di import extract_generic_type_key

        from .rabbit_connection import RabbitConnection

        # Extract configuration key from generic type arguments
        key = extract_generic_type_key(kwargs)

        # Get configuration options for this key
        options = service_provider.get_service(IOptions[key])

        # # The actual configuration is provided through options parameter
        return service_provider.create_instance(RabbitConnection, options=options, **kwargs)

    return service_container.add_transient(
        IRabbitConnection, factory=create_rabbit_connection)
