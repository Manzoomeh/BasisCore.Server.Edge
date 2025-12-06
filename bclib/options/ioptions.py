"""Options Interface for Configuration Access

Generic options interface for dependency injection to access application configuration.
Similar to ILogger pattern, provides type-safe access to specific configuration sections.
"""
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
    def value(self) -> Any:
        """
        Get configuration value

        Returns:
            Configuration value (can be dict, list, string, int, etc.)
        """
        raise NotImplementedError(
            "IOptions is an interface. Use Options class instead.")
