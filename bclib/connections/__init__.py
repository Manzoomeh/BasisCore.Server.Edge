"""Connection Module

Provides modern connection management inspired by ILogger<T> pattern.
Currently supports MongoDB and RabbitMQ with plans for SQL Server, PostgreSQL, Redis, and others.

Example:
    ```python
    from bclib.connections.mongo import IMongoConnection, add_mongodb_connection
    from bclib.connections.rabbit import IRabbitConnection, add_rabbitmq_connection
    
    # Register connections
    add_mongodb_connection(services)
    add_rabbitmq_connection(services)
    
    # Use in service
    class UserService:
        def __init__(
            self, 
            db: IMongoConnection['database.users'],
            rabbit: IRabbitConnection['rabbitmq.events']
        ):
            self.users = db.get_collection('users')
            self.rabbit = rabbit
    ```
"""

from .mongo import IMongoConnection
from .rabbit import IRabbitConnection

__all__ = ['add_connection_services', 'IMongoConnection', 'IRabbitConnection']


from bclib.di import IServiceContainer


def add_connection_services(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register All Connection Services in DI Container

    Adds connection services like MongoConnection and RabbitConnection as implementations
    for their respective interfaces in the service provider.
    This allows you to inject IMongoConnection[TConfig] and IRabbitConnection[TConfig]
    directly into your services without creating custom connection classes.

    Args:
        service_container: The service container to register services with

    Example:
        ```python
        from bclib import edge
        from bclib.connections import add_connection_services
        from bclib.connections.mongo import IMongoConnection
        from bclib.connections.rabbit import IRabbitConnection
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register all connection services
        add_connection_services(services)

        # Now both IMongoConnection[T] and IRabbitConnection[T] can be injected
        class UserService:
            def __init__(
                self, 
                db: IMongoConnection['database.users'],
                rabbit: IRabbitConnection['rabbitmq.events']
            ):
                self.users = db.get_collection('users')
                self.rabbit = rabbit

        # Configuration in appsettings.json:
        {
            "database": {
                "users": {
                    "connection_string": "mongodb://localhost:27017",
                    "database_name": "myapp_users"
                }
            },
            "rabbitmq": {
                "events": {
                    "url": "amqp://guest:guest@localhost:5672/",
                    "exchange": "events",
                    "exchange_type": "topic",
                    "routing_key": "user.events",
                    "durable": true
                }
            }
        }
        ```
    """
    from .mongo import add_mongodb_connection
    from .rabbit import add_rabbitmq_connection

    add_mongodb_connection(service_container)
    add_rabbitmq_connection(service_container)

    return service_container
