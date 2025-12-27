"""MongoDB Connection Module

Provides modern MongoDB database connection management inspired by ILogger<T> pattern.
No inheritance required - use IMongoConnection[TConfig] directly in your services.

Features:
    - Sync client support with MongoClient
    - Async client support with AsyncMongoClient
    - Lazy initialization for both sync and async clients
    - Type-safe configuration through generics
    - No inheritance required

Example:
    ```python
    from bclib.connections.mongo import IMongoConnection, add_mongodb_connection
    
    # Register MongoDB connections
    add_mongodb_connection(services)
    
    # Use in service (sync)
    class UserService:
        def __init__(self, db: IMongoConnection['database.users']):
            self.users = db.get_collection('users')
        
        def get_user(self, user_id: str):
            return self.users.find_one({'_id': user_id})
    
    # Use in service (async)
    class AsyncUserService:
        def __init__(self, db: IMongoConnection['database.users']):
            self.users = db.get_async_collection('users')
        
        async def get_user(self, user_id: str):
            return await self.users.find_one({'_id': user_id})
    ```
"""

from bclib.di import IServiceContainer

from .imongo_connection import IMongoConnection

__all__ = ['IMongoConnection', 'add_mongodb_connection']


def add_mongodb_connection(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register MongoDB Connection Services in DI Container

    Adds MongoConnection as the implementation for IMongoConnection[T] in the service provider.
    This allows you to inject IMongoConnection[TConfig] directly into your services without
    creating custom connection classes.

    Similar to add_logging for ILogger<T>, this function enables the ILogger-style pattern
    for MongoDB connections. Supports both sync (MongoClient) and async (AsyncMongoClient) operations.

    Args:
        service_container: The service container to register services with

    Returns:
        IServiceContainer: The service container for method chaining

    Example:
        ```python
        from bclib.connections.mongo import add_mongodb_connection
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register MongoDB connection services
        add_mongodb_connection(services)

        # Use sync in your services
        class UserService:
            def __init__(self, db: IMongoConnection['database.users']):
                self.db = db
                self.users = db.get_collection('users')

            def get_user(self, user_id: str):
                return self.users.find_one({'_id': user_id})

        # Use async in your services
        class AsyncUserService:
            def __init__(self, db: IMongoConnection['database.users']):
                self.db = db
                self.users = db.get_async_collection('users')

            async def get_user(self, user_id: str):
                return await self.users.find_one({'_id': user_id})

        # Configuration in appsettings.json:
        {
            "database": {
                "users": {
                    "connection_string": "mongodb://localhost:27017",
                    "database_name": "users_db",
                    "timeout": 5000,
                    "max_pool_size": 100
                }
            }
        }
        ```

    Note:
        After calling this function, you can inject IMongoConnection['your.config.key']
        into any service constructor. The DI container will automatically:
        1. Resolve configuration from 'your.config.key' 
        2. Create MongoConnection instance with those options
        3. Provide both sync (client) and async (async_client) MongoDB clients
        4. Inject it as IMongoConnection['your.config.key']
    """
    from bclib.di import IServiceProvider, extract_generic_type_key

    def create_mongo_connection(sp: IServiceProvider, **kwargs):
        """Factory for creating MongoConnection with configuration key from generic type"""
        from bclib.options import AppOptions
        from bclib.utility import resolve_dict_value

        from .mongo_connection import MongoConnection

        app_options = sp.get_service(AppOptions)
        key = extract_generic_type_key(kwargs)

        options = resolve_dict_value(key, app_options)
        if options is None:
            raise ValueError(
                f"MongoConnection configuration for key '{key}' not found.")
        return MongoConnection(options)
    return service_container.add_scoped(
        IMongoConnection, factory=create_mongo_connection)
