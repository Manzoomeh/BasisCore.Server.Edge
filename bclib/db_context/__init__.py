"""Database Context Module

Provides modern database context management inspired by ILogger<T> pattern.
Currently supports MongoDB with plans for SQL Server, PostgreSQL, and others.

Example:
    ```python
    from bclib.db_context.mongo import IMongoDbContext, add_mongodb
    
    # Register MongoDB contexts
    add_mongodb(services)
    
    # Use in service
    class UserService:
        def __init__(self, db: IMongoDbContext['database.users']):
            self.users = db.get_collection('users')
    ```
"""

__all__ = ['add_db_context_services']


from bclib.di import IServiceContainer


def add_db_context_services(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register Database Context Services in DI Container

    Adds database context services like MongoDbContext as the implementation for
    IMongoDbContext[T] in the service provider.
    This allows you to inject IMongoDbContext[TConfig] directly into your services without
    creating custom context classes.

    Args:
        service_container: The service container to register services with

    Example:
        ```python
        from bclib import edge
        from bclib.db_context.mongo import add_mongodb
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register MongoDB context services
        add_mongodb(services)

        # Now IMongoDbContext[T] can be injected in your services
        class UserService:
            def __init__(self, db: IMongoDbContext['database.users']):
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
    from .mongo import add_mongodb_default_context
    return add_mongodb_default_context(service_container)
