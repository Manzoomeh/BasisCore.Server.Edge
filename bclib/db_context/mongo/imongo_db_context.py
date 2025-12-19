from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from pymongo import AsyncMongoClient, MongoClient
    from pymongo.collection import Collection
    from pymongo.database import Database


T = TypeVar('T')


class IMongoDbContext(Generic[T], ABC):
    """
    MongoDB Context Interface - Similar to ILogger<T> pattern.

    Use this interface for dependency injection without inheritance.
    The generic type parameter T specifies the type of documents in the collection.

    Example:
        ```python
        class UserService:
            def __init__(self, db: IMongoDbContext['database.users']):
                self.db = db

            def get_users(self):
                return list(self.db.get_collection('users').find())
        ```

    Features:
        - No inheritance required
        - Type-safe configuration
        - Easy to mock in tests
        - Similar to ILogger<T> pattern
    """

    @property
    @abstractmethod
    def client(self) -> 'MongoClient':
        """Get MongoDB client instance."""
        pass

    @property
    @abstractmethod
    def async_client(self) -> 'AsyncMongoClient':
        """Get async MongoDB client instance."""
        pass

    @property
    @abstractmethod
    def database(self) -> 'Database':
        """Get MongoDB database instance."""
        pass

    @property
    @abstractmethod
    def async_database(self) -> 'Database':
        """Get async MongoDB database instance."""
        pass

    @abstractmethod
    def get_collection(self, collection_name: str) -> 'Collection':
        """Get a collection from the database."""
        pass

    @abstractmethod
    def get_async_collection(self, collection_name: str) -> 'Collection':
        """Get an async collection from the database."""
        pass

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, **options) -> 'Collection':
        """Create a new collection."""
        pass

    @abstractmethod
    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass
