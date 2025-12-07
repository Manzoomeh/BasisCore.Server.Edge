"""Options Interface for Configuration Access

Generic options interface for dependency injection to access application configuration.
Similar to ILogger pattern, provides type-safe access to specific configuration sections.
"""
from abc import abstractmethod, abstractproperty
from typing import Any, Generic, TypeVar

T = TypeVar('T')


class IOptions(Generic[T]):
    """
    Generic Options Interface

    Interface for type-safe configuration injection in constructors.
    The generic type parameter determines the configuration key to retrieve from AppOptions.

    Supports nested keys using dot notation (e.g., 'database.connection')

    Example:
        ```python
        # Access specific config key
        class DatabaseService:
            def __init__(self, options: IOptions['database']):
                self.config = options.value
                # If AppOptions = {'database': {'host': 'localhost', 'port': 5432}}
                # Then options.value = {'host': 'localhost', 'port': 5432}

        # Access nested config
        class RedisCache:
            def __init__(self, options: IOptions['cache.redis']):
                self.config = options.value
                # If AppOptions = {'cache': {'redis': {'host': 'localhost'}}}
                # Then options.value = {'host': 'localhost'}

        # Access entire config
        class ConfigMonitor:
            def __init__(self, options: IOptions['root']):
                self.all_config = options.value
                # Returns entire AppOptions dictionary
        ```
    """

    @property
    @abstractmethod
    def value(self) -> Any:
        """
        Get configuration value

        Returns:
            Configuration value (can be dict, list, string, int, etc.)
        """
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        """
        Get configuration value

        Returns:
            Configuration value (can be dict, list, string, int, etc.)
        """
        pass

    @property
    @abstractmethod
    def key(self) -> str:
        """Get configuration key"""
        pass

    @abstractmethod
    def get(self, nested_key: str, default: Any = None) -> Any:
        """
        Get nested value from configuration
        Case-sensitive first, then case-insensitive fallback for performance

        Args:
            nested_key: Nested key within this configuration section
            default: Default value if key not found

        Returns:
            Nested value or default

        Example:
            ```python
            # If options.value = {'host': 'localhost', 'port': 5432}
            host = options.get('host')  # 'localhost'
            host = options.get('HOST')  # 'localhost' (case-insensitive)
            timeout = options.get('timeout', 30)  # 30 (default)
            ```
        """
        pass
