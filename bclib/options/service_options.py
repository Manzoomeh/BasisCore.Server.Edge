from typing import Any, TypeVar

from .app_options import AppOptions
from .ioptions import IOptions

T = TypeVar('T')


class ServiceOptions(IOptions[T]):
    """
    Options Implementation

    Concrete implementation of IOptions interface.
    Resolves configuration values from AppOptions dictionary.
    """

    def __init__(self, key: str, app_options: AppOptions):
        """
        Initialize options with configuration key and app options

        Args:
            key: Configuration key (supports dot notation for nested access)
            app_options: Application options dictionary (AppOptions)
        """
        self._key = key
        self._app_options = app_options
        self._value = self._resolve_value(key, app_options)

    @staticmethod
    def _resolve_value(key: str, options: dict) -> Any:
        """
        Resolve value from options dictionary using key (supports dot notation)

        Args:
            key: Configuration key (e.g., 'database' or 'cache.redis')
            options: Options dictionary

        Returns:
            Configuration value or None if not found
        """
        if key == 'root':
            return options

        # Support dot notation for nested keys
        keys = key.split('.')
        value = options

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    @property
    def value(self) -> Any:
        """
        Get configuration value

        Returns:
            Configuration value (can be dict, list, string, int, etc.)
        """
        return self._value

    @property
    def key(self) -> str:
        """Get configuration key"""
        return self._key

    def get(self, nested_key: str, default: Any = None) -> Any:
        """
        Get nested value from configuration

        Args:
            nested_key: Nested key within this configuration section
            default: Default value if key not found

        Returns:
            Nested value or default

        Example:
            ```python
            # If options.value = {'host': 'localhost', 'port': 5432}
            host = options.get('host')  # 'localhost'
            timeout = options.get('timeout', 30)  # 30 (default)
            ```
        """
        if not isinstance(self._value, dict):
            return default

        return self._value.get(nested_key, default)

    def __repr__(self) -> str:
        return f"Options['{self._key}'](value={self._value})"
