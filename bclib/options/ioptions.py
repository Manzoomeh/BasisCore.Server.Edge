"""Options Interface for Configuration Access

Generic options interface for dependency injection to access application configuration.
Similar to ILogger pattern, provides type-safe access to specific configuration sections.
"""
from typing import Generic, TypeVar

T = TypeVar('T')


class IOptions(Generic[T], dict):
    """
    Generic Options Interface

    Interface for type-safe configuration injection in constructors.
    Inherits from dict for direct dictionary access.
    The generic type parameter determines the configuration key to retrieve from AppOptions.

    Supports nested keys using dot notation (e.g., 'database.connection')

    Example:
        ```python
        # Access specific config key
        class DatabaseService:
            def __init__(self, options: IOptions['database']):
                # Use as dict
                host = options['host']
                port = options.get('port', 5432)

                # Iterate
                for key, value in options.items():
                    print(f"{key}: {value}")

        # Access nested config
        class RedisCache:
            def __init__(self, options: IOptions['cache.redis']):
                self.host = options['host']
                self.port = options.get('port', 6379)

        # Access entire config
        class ConfigMonitor:
            def __init__(self, options: IOptions['']):
                for key in options:
                    print(key)
        ```
    """
    pass
