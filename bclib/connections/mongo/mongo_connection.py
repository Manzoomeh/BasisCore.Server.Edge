"""MongoDB Connection - Modern Database Management

A modern, flexible architecture for MongoDB management inspired by ILogger pattern.
Provides type-safe configuration injection through generic parameters.
No inheritance required - use directly like ILogger<T>.

Example:
    ```python
    # Use directly without inheritance (Recommended)
    class UserService:
        def __init__(self, db_connection: IMongoConnection['database.users']):
            self.db = db_connection
            
        async def get_user(self, user_id: str):
            users = self.db.get_collection('users')
            return await users.find_one({'_id': user_id})
    
    # Register in DI
    services.add_scoped_generic(IMongoConnection, MongoConnection)
    
    # Or register for specific configuration
    services.add_scoped(lambda sp: MongoConnection(sp.get(IOptions['database.users'])))
    ```

Configuration Example:
    ```json
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
"""

from typing import Any, Dict, Optional, TypeVar

from pymongo import AsyncMongoClient, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from bclib.options import IOptions

from .imongo_connection import IMongoConnection

T = TypeVar('T')


class MongoConnection(IMongoConnection[T]):
    """
    MongoDB Connection Implementation - Use directly without inheritance.

    This is the concrete implementation of IMongoConnection.
    Similar to Logger<T> in .NET, you don't need to inherit from this class.

    Generic type parameter TConfig specifies the configuration key to retrieve
    from IOptions during dependency injection.

    Usage:
        ```python
        # Direct injection (Recommended - ILogger style)
        class UserService:
            def __init__(self, db: IMongoConnection['database.users']):
                self.db = db
                self.users = db.get_collection('users')

        # Or if you prefer storing collections as properties
        class ProductService:
            def __init__(self, db: IMongoConnection['database.products']):
                self.db = db
                # Cache collections as instance variables
                self.products = db.get_collection('products')
                self.categories = db.get_collection('categories')
        ```

    Features:
        - Type-safe configuration through generics
        - Lazy connection initialization
        - Database and collection access
        - Context manager support
        - Connection pooling
        - No inheritance required

    Attributes:
        connection_string (str): MongoDB connection string
        database_name (str): Target database name
        client (MongoClient): MongoDB client instance
        database (Database): MongoDB database instance
    """

    def __init__(self, options: IOptions[T]):
        """
        Initialize MongoDB connection with configuration options.

        Args:
            options: Configuration options containing connection details

        Required configuration keys:
            - connection_string: MongoDB connection URI
            - database_name: Target database name

        Optional configuration keys:
            - timeout: Connection timeout in milliseconds (default: 5000)
            - max_pool_size: Maximum connection pool size (default: 100)
            - min_pool_size: Minimum connection pool size (default: 0)
            - server_selection_timeout: Server selection timeout in ms (default: 30000)

        Raises:
            KeyError: If required configuration keys are missing
            ValueError: If configuration values are invalid
        """
        self._options = options
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        self._async_client: Optional[AsyncMongoClient] = None
        self._async_database: Optional[Database] = None

        # Validate required configuration
        self._validate_options()

    def _validate_options(self) -> None:
        """Validate required configuration options."""
        if 'connection_string' not in self._options:
            raise KeyError(
                "Configuration key 'connection_string' is required for MongoDB connection. "
                "Please ensure your configuration contains this key."
            )

        if 'database_name' not in self._options:
            raise KeyError(
                "Configuration key 'database_name' is required for MongoDB connection. "
                "Please ensure your configuration contains this key."
            )

    @property
    def client(self) -> MongoClient:
        """
        Get or create MongoDB client instance (lazy initialization).

        Returns:
            MongoClient: Active MongoDB client
        """
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @property
    def async_client(self) -> AsyncMongoClient:
        """
        Get or create async MongoDB client instance (lazy initialization).

        Returns:
            AsyncMongoClient: Active async MongoDB client
        """
        if self._async_client is None:
            self._async_client = self._create_async_client()
        return self._async_client

    @property
    def database(self) -> Database:
        """
        Get or create MongoDB database instance (lazy initialization).

        Returns:
            Database: Active MongoDB database
        """
        if self._database is None:
            database_name = self._options['database_name']
            self._database = self.client[database_name]
        return self._database

    @property
    def async_database(self) -> Database:
        """
        Get or create async MongoDB database instance (lazy initialization).

        Returns:
            Database: Active async MongoDB database
        """
        if self._async_database is None:
            database_name = self._options['database_name']
            self._async_database = self.async_client[database_name]
        return self._async_database

    def _create_client(self) -> MongoClient:
        """
        Create MongoDB client with configuration options.

        Returns:
            MongoClient: Configured MongoDB client
        """
        connection_string = self._options['connection_string']

        # Build client options from configuration
        client_options: Dict[str, Any] = {}

        if 'timeout' in self._options:
            client_options['connectTimeoutMS'] = self._options['timeout']

        if 'max_pool_size' in self._options:
            client_options['maxPoolSize'] = self._options['max_pool_size']

        if 'min_pool_size' in self._options:
            client_options['minPoolSize'] = self._options['min_pool_size']

        if 'server_selection_timeout' in self._options:
            client_options['serverSelectionTimeoutMS'] = self._options['server_selection_timeout']

        return MongoClient(connection_string, **client_options)

    def _create_async_client(self) -> AsyncMongoClient:
        """
        Create async MongoDB client with configuration options.

        Returns:
            AsyncMongoClient: Configured async MongoDB client
        """
        connection_string = self._options['connection_string']

        # Build client options from configuration
        client_options: Dict[str, Any] = {}

        if 'timeout' in self._options:
            client_options['connectTimeoutMS'] = self._options['timeout']

        if 'max_pool_size' in self._options:
            client_options['maxPoolSize'] = self._options['max_pool_size']

        if 'min_pool_size' in self._options:
            client_options['minPoolSize'] = self._options['min_pool_size']

        if 'server_selection_timeout' in self._options:
            client_options['serverSelectionTimeoutMS'] = self._options['server_selection_timeout']

        return AsyncMongoClient(connection_string, **client_options)

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection from the database.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection: MongoDB collection instance

        Example:
            ```python
            users = self.get_collection('users')
            user = users.find_one({'email': 'test@example.com'})
            ```
        """
        return self.database[collection_name]

    def get_async_collection(self, collection_name: str) -> Collection:
        """
        Get an async collection from the database.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection: Async MongoDB collection instance

        Example:
            ```python
            users = self.get_async_collection('users')
            user = await users.find_one({'email': 'test@example.com'})
            ```
        """
        return self.async_database[collection_name]

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists in the database.

        Args:
            collection_name: Name of the collection to check

        Returns:
            bool: True if collection exists, False otherwise
        """
        return collection_name in self.database.list_collection_names()

    def create_collection(self, collection_name: str, **options) -> Collection:
        """
        Create a new collection in the database.

        Args:
            collection_name: Name of the collection to create
            **options: Additional options for collection creation

        Returns:
            Collection: Newly created collection

        Example:
            ```python
            # Create capped collection
            logs = self.create_collection('logs', capped=True, size=10000)
            ```
        """
        return self.database.create_collection(collection_name, **options)

    def drop_collection(self, collection_name: str) -> None:
        """
        Drop a collection from the database.

        Args:
            collection_name: Name of the collection to drop

        Warning:
            This operation cannot be undone!
        """
        self.database.drop_collection(collection_name)

    def close(self) -> None:
        """
        Close the MongoDB client connections (sync and async).

        Note:
            Connection will be automatically closed when used as context manager.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None

        if self._async_client is not None:
            self._async_client.close()
            self._async_client = None
            self._async_database = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection cleanup."""
        self.close()
        return False

    def __repr__(self) -> str:
        """String representation of the connection."""
        database_name = self._options.get('database_name', 'unknown')
        return f"<{self.__class__.__name__} database='{database_name}'>"
