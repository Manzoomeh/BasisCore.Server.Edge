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
        Case-sensitive first, then case-insensitive fallback for performance

        Args:
            key: Configuration key (e.g., 'database' or 'cache.redis')
            options: Options dictionary

        Returns:
            Configuration value or None if not found
        """
        if key == '':
            return options

        # Support dot notation for nested keys
        keys = key.split('.')
        value = options

        for k in keys:
            if isinstance(value, dict):
                # Try case-sensitive lookup first (fast path)
                if k in value:
                    value = value[k]
                else:
                    # Fallback to case-insensitive lookup
                    matched_key = None
                    k_lower = k.lower()
                    for dict_key in value.keys():
                        if dict_key.lower() == k_lower:
                            matched_key = dict_key
                            break

                    if matched_key:
                        value = value[matched_key]
                    else:
                        return None
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
        if not isinstance(self._value, dict):
            return default

        # Try case-sensitive lookup first (fast path)
        if nested_key in self._value:
            return self._value[nested_key]

        # Fallback to case-insensitive lookup
        nested_key_lower = nested_key.lower()
        for key in self._value.keys():
            if key.lower() == nested_key_lower:
                return self._value[key]

        return default

    def __repr__(self) -> str:
        return f"Options['{self._key}'](value={self._value})"
