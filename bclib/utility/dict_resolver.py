"""Dictionary Value Resolver Utility

Provides utilities for resolving nested dictionary values using dot notation.
Supports both case-sensitive and case-insensitive key lookups.
"""
from typing import Any, Optional


def resolve_dict_value(key: str, data: dict, case_sensitive: bool = False) -> Any:
    """
    Resolve value from dictionary using key with dot notation support.

    This utility function allows accessing nested dictionary values using dot notation
    (e.g., 'database.users.connection_string'). It supports both case-sensitive and
    case-insensitive key lookups.

    Performance optimizations:
    - Empty key returns entire dictionary
    - Case-sensitive lookup first (fast path)
    - Case-insensitive fallback only when needed
    - Short-circuit on first match

    Args:
        key: Configuration key supporting dot notation
             Examples:
             - '' (empty string): returns entire dictionary
             - 'database': returns data['database']
             - 'database.users': returns data['database']['users']
             - 'cache.redis.host': returns data['cache']['redis']['host']
        data: Dictionary to resolve value from
        case_sensitive: If False, always uses case-insensitive lookup.
                       If True (default), tries case-sensitive first, then case-insensitive fallback.

    Returns:
        Resolved value at the specified key path, or None if not found.
        Returns the entire dictionary if key is empty string.

    Examples:
        ```python
        config = {
            'database': {
                'users': {
                    'connection_string': 'mongodb://localhost:27017',
                    'database_name': 'users_db'
                }
            },
            'Cache': {  # Note: capital C
                'Redis': {  # Note: capital R
                    'Host': 'localhost'  # Note: capital H
                }
            }
        }

        # Empty key returns entire dictionary
        resolve_dict_value('', config)
        # Returns: entire config dict

        # Simple key
        resolve_dict_value('database', config)
        # Returns: {'users': {...}}

        # Nested key with dot notation
        resolve_dict_value('database.users.connection_string', config)
        # Returns: 'mongodb://localhost:27017'

        # Case-sensitive (default) - tries case-sensitive first, then case-insensitive
        resolve_dict_value('cache.redis.host', config)
        # Returns: 'localhost' (found via case-insensitive fallback)

        # Case-insensitive mode
        resolve_dict_value('CACHE.REDIS.HOST', config, case_sensitive=False)
        # Returns: 'localhost'

        # Key not found
        resolve_dict_value('nonexistent.key', config)
        # Returns: None

        # Partial path that doesn't exist
        resolve_dict_value('database.products', config)
        # Returns: None
        ```

    Note:
        - For best performance, use exact case matching when possible
        - Case-insensitive lookup is slower due to string comparison overhead
        - Returns None for any path that doesn't exist or encounters non-dict values
    """
    # Handle empty key - return entire dictionary
    if key == '':
        return data

    # Split key by dots for nested access
    keys = key.split('.')
    current_value = data

    # Traverse the dictionary following the key path
    for k in keys:
        # Ensure current value is a dictionary before attempting key access
        if not isinstance(current_value, dict):
            return None

        # Try case-sensitive lookup first (fast path)
        if case_sensitive and k in current_value:
            current_value = current_value[k]
        else:
            # Fallback to case-insensitive lookup
            matched_key = None
            k_lower = k.lower()

            # Search for case-insensitive match
            for dict_key in current_value.keys():
                if dict_key.lower() == k_lower:
                    matched_key = dict_key
                    break

            if matched_key:
                current_value = current_value[matched_key]
            else:
                # Key not found in current level
                return None

    return current_value


def resolve_dict_value_with_default(
    key: str,
    data: dict,
    default: Any = None,
    case_sensitive: bool = True
) -> Any:
    """
    Resolve value from dictionary with a default fallback.

    Similar to resolve_dict_value but returns a default value instead of None
    when the key is not found.

    Args:
        key: Configuration key supporting dot notation
        data: Dictionary to resolve value from
        default: Default value to return if key is not found
        case_sensitive: If False, always uses case-insensitive lookup

    Returns:
        Resolved value at the specified key path, or default if not found

    Examples:
        ```python
        config = {'database': {'timeout': 5000}}

        # Existing key
        resolve_dict_value_with_default('database.timeout', config, 3000)
        # Returns: 5000

        # Non-existing key
        resolve_dict_value_with_default('database.max_pool_size', config, 100)
        # Returns: 100

        # Non-existing key with None default (same as resolve_dict_value)
        resolve_dict_value_with_default('database.host', config)
        # Returns: None
        ```
    """
    result = resolve_dict_value(key, data, case_sensitive)
    return default if result is None else result


def has_dict_key(key: str, data: dict, case_sensitive: bool = True) -> bool:
    """
    Check if a key exists in dictionary (supports dot notation).

    Args:
        key: Configuration key supporting dot notation
        data: Dictionary to check
        case_sensitive: If False, uses case-insensitive lookup

    Returns:
        True if key exists and is not None, False otherwise

    Examples:
        ```python
        config = {'database': {'users': {'host': 'localhost'}}}

        has_dict_key('database.users.host', config)
        # Returns: True

        has_dict_key('database.products', config)
        # Returns: False

        has_dict_key('DATABASE.USERS.HOST', config, case_sensitive=False)
        # Returns: True
        ```
    """
    return resolve_dict_value(key, data, case_sensitive) is not None


def get_dict_keys_at_path(key: str, data: dict, case_sensitive: bool = True) -> Optional[list]:
    """
    Get all keys at a specific path in dictionary.

    Args:
        key: Configuration key path (use '' for root level)
        data: Dictionary to query
        case_sensitive: If False, uses case-insensitive lookup

    Returns:
        List of keys at the specified path, or None if path doesn't exist or isn't a dict

    Examples:
        ```python
        config = {
            'database': {
                'users': {'host': 'localhost', 'port': 27017},
                'products': {'host': 'localhost', 'port': 27017}
            }
        }

        # Get root keys
        get_dict_keys_at_path('', config)
        # Returns: ['database']

        # Get keys at nested path
        get_dict_keys_at_path('database', config)
        # Returns: ['users', 'products']

        # Get keys at deeper path
        get_dict_keys_at_path('database.users', config)
        # Returns: ['host', 'port']

        # Path doesn't exist
        get_dict_keys_at_path('database.logs', config)
        # Returns: None
        ```
    """
    value = resolve_dict_value(key, data, case_sensitive)

    if isinstance(value, dict):
        return list(value.keys())

    return None
