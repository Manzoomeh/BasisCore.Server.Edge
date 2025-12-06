"""Database Manager Interface"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.db_manager.db import Db
    from bclib.db_manager.mongo_db import MongoDb
    from bclib.db_manager.rabbit_connection import RabbitConnection
    from bclib.db_manager.restful_connection import RESTfulConnection
    from bclib.db_manager.sql_db import SqlDb
    from bclib.db_manager.sqlite_db import SQLiteDb


class IDbManager(ABC):
    """
    Interface for database connection management

    Provides methods to open various types of database connections
    based on configuration settings.
    """

    @abstractmethod
    def open_connection(self, key: str) -> 'Db':
        """
        Open a database connection by configuration key

        Args:
            key: Configuration key for the connection

        Returns:
            Db: Database connection instance

        Raises:
            Exception: If connection settings not found
        """
        pass

    @abstractmethod
    def open_sql_connection(self, key: str) -> 'SqlDb':
        """
        Open a SQL database connection

        Args:
            key: Configuration key for the SQL connection

        Returns:
            SqlDb: SQL database connection instance
        """
        pass

    @abstractmethod
    def open_sqllite_connection(self, key: str) -> 'SQLiteDb':
        """
        Open a SQLite database connection

        Args:
            key: Configuration key for the SQLite connection

        Returns:
            SQLiteDb: SQLite database connection instance
        """
        pass

    @abstractmethod
    def open_mongo_connection(self, key: str) -> 'MongoDb':
        """
        Open a MongoDB connection

        Args:
            key: Configuration key for the MongoDB connection

        Returns:
            MongoDb: MongoDB connection instance
        """
        pass

    @abstractmethod
    def open_restful_connection(self, key: str) -> 'RESTfulConnection':
        """
        Open a RESTful API connection

        Args:
            key: Configuration key for the RESTful connection

        Returns:
            RESTfulConnection: RESTful connection instance
        """
        pass

    @abstractmethod
    def open_rabbit_connection(self, key: str) -> 'RabbitConnection':
        """
        Open a RabbitMQ connection

        Args:
            key: Configuration key for the RabbitMQ connection

        Returns:
            RabbitConnection: RabbitMQ connection instance
        """
        pass
