"""Unit Tests for Dictionary Resolver Utility

Tests for resolve_dict_value and related utility functions.
"""

import unittest

from bclib.utility import (get_dict_keys_at_path, has_dict_key,
                           resolve_dict_value, resolve_dict_value_with_default)


class TestResolveDictValue(unittest.TestCase):
    """Test suite for resolve_dict_value function"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'database': {
                'users': {
                    'connection_string': 'mongodb://localhost:27017',
                    'database_name': 'users_db',
                    'timeout': 5000,
                    'max_pool_size': 100
                },
                'products': {
                    'connection_string': 'mongodb://localhost:27017',
                    'database_name': 'products_db'
                }
            },
            'Cache': {  # Note: capital C
                'Redis': {  # Note: capital R
                    'Host': 'localhost',  # Note: capital H
                    'Port': 6379
                }
            },
            'simple_key': 'simple_value',
            'number': 42,
            'boolean': True,
            'list': [1, 2, 3]
        }

    def test_empty_key_returns_entire_dict(self):
        """Test that empty key returns entire dictionary"""
        result = resolve_dict_value('', self.config)
        self.assertEqual(result, self.config)

    def test_simple_key(self):
        """Test simple single-level key access"""
        result = resolve_dict_value('simple_key', self.config)
        self.assertEqual(result, 'simple_value')

    def test_nested_key_with_dots(self):
        """Test nested key access using dot notation"""
        result = resolve_dict_value(
            'database.users.connection_string', self.config)
        self.assertEqual(result, 'mongodb://localhost:27017')

    def test_nested_key_returns_dict(self):
        """Test that nested key can return a dictionary"""
        result = resolve_dict_value('database.users', self.config)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['database_name'], 'users_db')

    def test_case_sensitive_with_exact_match(self):
        """Test case-sensitive lookup with exact case match"""
        result = resolve_dict_value(
            'Cache.Redis.Host', self.config, case_sensitive=True)
        self.assertEqual(result, 'localhost')

    def test_case_sensitive_with_fallback(self):
        """Test case-sensitive mode falls back to case-insensitive"""
        # Lower case key should still find 'Cache.Redis.Host' via fallback
        result = resolve_dict_value(
            'cache.redis.host', self.config, case_sensitive=True)
        self.assertEqual(result, 'localhost')

    def test_case_insensitive_mode(self):
        """Test case-insensitive lookup mode"""
        result = resolve_dict_value(
            'CACHE.REDIS.PORT', self.config, case_sensitive=False)
        self.assertEqual(result, 6379)

    def test_nonexistent_key_returns_none(self):
        """Test that nonexistent key returns None"""
        result = resolve_dict_value('nonexistent', self.config)
        self.assertIsNone(result)

    def test_nonexistent_nested_key_returns_none(self):
        """Test that nonexistent nested key returns None"""
        result = resolve_dict_value('database.logs', self.config)
        self.assertIsNone(result)

    def test_partial_path_to_non_dict_returns_none(self):
        """Test that accessing nested key on non-dict value returns None"""
        result = resolve_dict_value('simple_key.nested', self.config)
        self.assertIsNone(result)

    def test_number_value(self):
        """Test retrieving number value"""
        result = resolve_dict_value('number', self.config)
        self.assertEqual(result, 42)

    def test_boolean_value(self):
        """Test retrieving boolean value"""
        result = resolve_dict_value('boolean', self.config)
        self.assertTrue(result)

    def test_list_value(self):
        """Test retrieving list value"""
        result = resolve_dict_value('list', self.config)
        self.assertEqual(result, [1, 2, 3])

    def test_deep_nesting(self):
        """Test very deep nesting"""
        deep_config = {'a': {'b': {'c': {'d': {'e': 'deep_value'}}}}}
        result = resolve_dict_value('a.b.c.d.e', deep_config)
        self.assertEqual(result, 'deep_value')


class TestResolveDictValueWithDefault(unittest.TestCase):
    """Test suite for resolve_dict_value_with_default function"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'database': {
                'timeout': 5000,
                'max_pool_size': 100
            }
        }

    def test_existing_key_returns_value(self):
        """Test that existing key returns actual value, not default"""
        result = resolve_dict_value_with_default(
            'database.timeout', self.config, 3000)
        self.assertEqual(result, 5000)

    def test_nonexistent_key_returns_default(self):
        """Test that nonexistent key returns default value"""
        result = resolve_dict_value_with_default(
            'database.min_pool_size', self.config, 10)
        self.assertEqual(result, 10)

    def test_default_none(self):
        """Test that None can be used as default"""
        result = resolve_dict_value_with_default('nonexistent', self.config)
        self.assertIsNone(result)

    def test_default_string(self):
        """Test default with string value"""
        result = resolve_dict_value_with_default(
            'database.host', self.config, 'localhost')
        self.assertEqual(result, 'localhost')

    def test_default_dict(self):
        """Test default with dict value"""
        default_dict = {'host': 'localhost', 'port': 27017}
        result = resolve_dict_value_with_default(
            'database.mongo', self.config, default_dict)
        self.assertEqual(result, default_dict)


class TestHasDictKey(unittest.TestCase):
    """Test suite for has_dict_key function"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'database': {
                'users': {
                    'host': 'localhost',
                    'port': 27017
                }
            },
            'Cache': {
                'Redis': {
                    'Host': 'localhost'
                }
            }
        }

    def test_existing_key_returns_true(self):
        """Test that existing key returns True"""
        self.assertTrue(has_dict_key('database.users.host', self.config))

    def test_nonexistent_key_returns_false(self):
        """Test that nonexistent key returns False"""
        self.assertFalse(has_dict_key('database.products', self.config))

    def test_case_insensitive_match(self):
        """Test case-insensitive key check"""
        self.assertTrue(has_dict_key('cache.redis.host',
                        self.config, case_sensitive=False))

    def test_partial_path_returns_true(self):
        """Test that partial path to dict returns True"""
        self.assertTrue(has_dict_key('database.users', self.config))

    def test_empty_key_returns_true(self):
        """Test that empty key returns True (entire dict exists)"""
        self.assertTrue(has_dict_key('', self.config))


class TestGetDictKeysAtPath(unittest.TestCase):
    """Test suite for get_dict_keys_at_path function"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'database': {
                'users': {'host': 'localhost', 'port': 27017},
                'products': {'host': 'localhost', 'port': 27017}
            },
            'cache': {
                'redis': {'host': 'localhost', 'port': 6379}
            }
        }

    def test_root_level_keys(self):
        """Test getting keys at root level"""
        result = get_dict_keys_at_path('', self.config)
        self.assertEqual(set(result), {'database', 'cache'})

    def test_nested_level_keys(self):
        """Test getting keys at nested level"""
        result = get_dict_keys_at_path('database', self.config)
        self.assertEqual(set(result), {'users', 'products'})

    def test_deep_nested_keys(self):
        """Test getting keys at deeper level"""
        result = get_dict_keys_at_path('database.users', self.config)
        self.assertEqual(set(result), {'host', 'port'})

    def test_nonexistent_path_returns_none(self):
        """Test that nonexistent path returns None"""
        result = get_dict_keys_at_path('database.logs', self.config)
        self.assertIsNone(result)

    def test_path_to_non_dict_returns_none(self):
        """Test that path to non-dict value returns None"""
        result = get_dict_keys_at_path('database.users.host', self.config)
        self.assertIsNone(result)


class TestPerformance(unittest.TestCase):
    """Test suite for performance characteristics"""

    def test_case_sensitive_is_faster(self):
        """Test that case-sensitive lookup is used when keys match exactly"""
        large_config = {f'key{i}': f'value{i}' for i in range(1000)}
        large_config['target'] = 'found'

        # This should use fast path (exact match)
        result = resolve_dict_value(
            'target', large_config, case_sensitive=True)
        self.assertEqual(result, 'found')


class TestEdgeCases(unittest.TestCase):
    """Test suite for edge cases"""

    def test_empty_dict(self):
        """Test with empty dictionary"""
        result = resolve_dict_value('key', {})
        self.assertIsNone(result)

    def test_none_value_in_dict(self):
        """Test that None value is returned correctly"""
        config = {'key': None}
        result = resolve_dict_value('key', config)
        self.assertIsNone(result)

    def test_zero_value(self):
        """Test that zero value is returned correctly"""
        config = {'count': 0}
        result = resolve_dict_value('count', config)
        self.assertEqual(result, 0)

    def test_false_value(self):
        """Test that False value is returned correctly"""
        config = {'enabled': False}
        result = resolve_dict_value('enabled', config)
        self.assertFalse(result)

    def test_empty_string_value(self):
        """Test that empty string value is returned correctly"""
        config = {'name': ''}
        result = resolve_dict_value('name', config)
        self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
