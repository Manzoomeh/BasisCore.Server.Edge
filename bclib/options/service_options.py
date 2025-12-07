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
        # Resolve value
        value = self._resolve_value(key, app_options)

        # Initialize dict with resolved value if it's a dict
        if isinstance(value, dict):
            super().__init__(value)
        else:
            super().__init__()

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
