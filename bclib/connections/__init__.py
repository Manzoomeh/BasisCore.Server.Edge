"""Database Connection Module

Provides modern database connection management inspired by ILogger<T> pattern.
Currently supports MongoDB with plans for SQL Server, PostgreSQL, and others.

Example:
    ```python
    from bclib.connections.mongo import IMongoConnection, add_mongodb_connection
    
    # Register MongoDB connections
    add_mongodb_connection(services)
    
    # Use in service
    class UserService:
        def __init__(self, db: IMongoConnection['database.users']):
            self.users = db.get_collection('users')
    ```
"""

from .mongo import IMongoConnection

__all__ = ['add_connection_services', 'IMongoConnection']


from bclib.di import IServiceContainer


def add_connection_services(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register Database Connection Services in DI Container

    Adds database connection services like MongoConnection as the implementation for
    IMongoConnection[T] in the service provider.
    This allows you to inject IMongoConnection[TConfig] directly into your services without
    creating custom connection classes.

    Args:
        service_container: The service container to register services with

    Example:
        ```python
        from bclib import edge
        from bclib.connections.mongo import add_mongodb_connection
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register MongoDB connection services
        add_mongodb_connection(services)

        # Now IMongoConnection[T] can be injected in your services
        class UserService:
            def __init__(self, db: IMongoConnection['database.users']):
                self.db = db
                self.users = db.get_collection('users')

        # Configuration in appsettings.json:
        {
            "database": {
                "users": {
                    "connection_string": "mongodb://localhost:27017",
                    "database_name": "myapp_users"
                }
            }
        }
        ```
    """
    from .mongo import add_mongodb_connection
    return add_mongodb_connection(service_container)
