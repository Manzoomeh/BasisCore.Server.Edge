"""MongoDB Context Module

Provides modern MongoDB database context management inspired by ILogger<T> pattern.
No inheritance required - use IMongoDbContext[TConfig] directly in your services.

Features:
    - Sync client support with MongoClient
    - Async client support with AsyncMongoClient
    - Lazy initialization for both sync and async clients
    - Type-safe configuration through generics
    - No inheritance required

Example:
    ```python
    from bclib.db_context.mongo import IMongoDbContext, add_mongodb_default_context
    
    # Register MongoDB contexts
    add_mongodb_default_context(services)
    
    # Use in service (sync)
    class UserService:
        def __init__(self, db: IMongoDbContext['database.users']):
            self.users = db.get_collection('users')
        
        def get_user(self, user_id: str):
            return self.users.find_one({'_id': user_id})
    
    # Use in service (async)
    class AsyncUserService:
        def __init__(self, db: IMongoDbContext['database.users']):
            self.users = db.get_async_collection('users')
        
        async def get_user(self, user_id: str):
            return await self.users.find_one({'_id': user_id})
    ```
"""
from typing import ForwardRef

from bclib.di import IServiceContainer, IServiceProvider

from .imongo_db_context import IMongoDbContext

__all__ = ['IMongoDbContext', 'add_mongodb_default_context']


def add_mongodb_default_context(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register MongoDB Context Services in DI Container

    Adds MongoDbContext as the implementation for IMongoDbContext[T] in the service provider.
    This allows you to inject IMongoDbContext[TConfig] directly into your services without
    creating custom context classes.

    Similar to add_logging for ILogger<T>, this function enables the ILogger-style pattern
    for MongoDB contexts. Supports both sync (MongoClient) and async (AsyncMongoClient) operations.

    Args:
        service_container: The service container to register services with

    Returns:
        IServiceContainer: The service container for method chaining

    Example:
        ```python
        from bclib.db_context.mongo import add_mongodb_default_context
        from bclib.di import ServiceProvider

        # Create DI container
        services = ServiceProvider()

        # Register MongoDB context services
        add_mongodb_default_context(services)

        # Use sync in your services
        class UserService:
            def __init__(self, db: IMongoDbContext['database.users']):
                self.db = db
                self.users = db.get_collection('users')

            def get_user(self, user_id: str):
                return self.users.find_one({'_id': user_id})

        # Use async in your services
        class AsyncUserService:
            def __init__(self, db: IMongoDbContext['database.users']):
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
        After calling this function, you can inject IMongoDbContext['your.config.key']
        into any service constructor. The DI container will automatically:
        1. Resolve configuration from 'your.config.key' 
        2. Create MongoDbContext instance with those options
        3. Provide both sync (client) and async (async_client) MongoDB clients
        4. Inject it as IMongoDbContext['your.config.key']
    """
    def create_mongo_db_context(sp: IServiceProvider, **kwargs):
        """Factory for creating MongoDbContext with configuration key from generic type"""
        from bclib.options import AppOptions
        from bclib.utility import resolve_dict_value

        from .mongo_db_context import MongoDbContext

        app_options = sp.get_service(AppOptions)
        type_args: tuple[type, ...] = kwargs.get('generic_type_args', ('',))
        key: str = None

        # Extract class name from ForwardRef or type
        key_source = type_args[0]

        if isinstance(key_source, ForwardRef):
            # ForwardRef: extract the string representation
            key = key_source.__forward_arg__
        elif isinstance(key_source, type):
            # Actual class: use __name__
            key = key_source.__name__
        elif isinstance(key_source, str):
            # Already a string
            key = key_source
        else:
            # Fallback to string representation
            key = str(key_source)
        options = resolve_dict_value(key, app_options)
        if (options is None):
            raise ValueError(
                f"MongoDbContext configuration for key '{key}' not found.")
        return MongoDbContext(options)
    return service_container.add_scoped(
        IMongoDbContext, factory=create_mongo_db_context)
