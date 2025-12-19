"""Unit Tests for MongoDbContext

Complete test suite demonstrating usage and verifying functionality.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from bclib.db_manager.mongo_db_context import (MongoDbContext,
                                               MongoDbContextFactory)
from bclib.options.ioptions import IOptions


# Test Context Implementation
class TestDbContext(MongoDbContext['test.database']):
    """Test database context"""

    def __init__(self, options: IOptions['test.database']):
        super().__init__(options)

    @property
    def test_collection(self):
        return self.get_collection('test_collection')


class TestMongoDbContext(unittest.TestCase):
    """Test suite for MongoDbContext"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_options: IOptions['test.database'] = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'test_db',
            'timeout': 5000,
            'max_pool_size': 50
        }

    def test_context_initialization(self):
        """Test context initializes with valid options"""
        context = TestDbContext(self.test_options)

        self.assertIsNotNone(context)
        self.assertEqual(context._options, self.test_options)

    def test_missing_connection_string_raises_error(self):
        """Test that missing connection_string raises KeyError"""
        invalid_options: IOptions['test.database'] = {
            'database_name': 'test_db'
        }

        with self.assertRaises(KeyError) as context:
            TestDbContext(invalid_options)

        self.assertIn('connection_string', str(context.exception))

    def test_missing_database_name_raises_error(self):
        """Test that missing database_name raises KeyError"""
        invalid_options: IOptions['test.database'] = {
            'connection_string': 'mongodb://localhost:27017'
        }

        with self.assertRaises(KeyError) as context:
            TestDbContext(invalid_options)

        self.assertIn('database_name', str(context.exception))

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_lazy_client_initialization(self, mock_client):
        """Test that client is initialized lazily"""
        context = TestDbContext(self.test_options)

        # Client should not be created yet
        self.assertIsNone(context._client)
        mock_client.assert_not_called()

        # Access client property
        client = context.client

        # Now client should be created
        mock_client.assert_called_once()
        self.assertIsNotNone(client)

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_client_configuration_options(self, mock_client):
        """Test that client is created with correct options"""
        context = TestDbContext(self.test_options)
        _ = context.client

        # Verify client was called with correct parameters
        mock_client.assert_called_once_with(
            'mongodb://localhost:27017',
            connectTimeoutMS=5000,
            maxPoolSize=50
        )

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_database_property(self, mock_client):
        """Test database property returns correct database"""
        mock_db = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_client.return_value = mock_client_instance

        context = TestDbContext(self.test_options)
        database = context.database

        # Verify database was accessed with correct name
        mock_client_instance.__getitem__.assert_called_with('test_db')
        self.assertEqual(database, mock_db)

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_get_collection(self, mock_client):
        """Test get_collection returns correct collection"""
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_client.return_value = mock_client_instance

        context = TestDbContext(self.test_options)
        collection = context.get_collection('users')

        # Verify collection was accessed
        mock_db.__getitem__.assert_called_with('users')
        self.assertEqual(collection, mock_collection)

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_collection_exists(self, mock_client):
        """Test collection_exists method"""
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = [
            'users', 'products', 'orders']

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_client.return_value = mock_client_instance

        context = TestDbContext(self.test_options)

        self.assertTrue(context.collection_exists('users'))
        self.assertTrue(context.collection_exists('products'))
        self.assertFalse(context.collection_exists('nonexistent'))

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_create_collection(self, mock_client):
        """Test create_collection method"""
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.create_collection.return_value = mock_collection

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_client.return_value = mock_client_instance

        context = TestDbContext(self.test_options)
        collection = context.create_collection(
            'new_collection', capped=True, size=1000)

        # Verify collection was created with options
        mock_db.create_collection.assert_called_with(
            'new_collection',
            capped=True,
            size=1000
        )
        self.assertEqual(collection, mock_collection)

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_drop_collection(self, mock_client):
        """Test drop_collection method"""
        mock_db = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_client.return_value = mock_client_instance

        context = TestDbContext(self.test_options)
        context.drop_collection('old_collection')

        # Verify collection was dropped
        mock_db.drop_collection.assert_called_with('old_collection')

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_close_method(self, mock_client):
        """Test close method closes client"""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        context = TestDbContext(self.test_options)

        # Initialize client
        _ = context.client

        # Close context
        context.close()

        # Verify client was closed and cleared
        mock_client_instance.close.assert_called_once()
        self.assertIsNone(context._client)
        self.assertIsNone(context._database)

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_context_manager(self, mock_client):
        """Test context can be used as context manager"""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        with TestDbContext(self.test_options) as context:
            # Use context
            _ = context.client
            self.assertIsNotNone(context._client)

        # Verify client was closed after exiting context
        mock_client_instance.close.assert_called_once()

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_repr_method(self, mock_client):
        """Test string representation"""
        context = TestDbContext(self.test_options)
        repr_string = repr(context)

        self.assertIn('TestDbContext', repr_string)
        self.assertIn('test_db', repr_string)

    def test_factory_create(self):
        """Test factory creates context correctly"""
        factory = MongoDbContextFactory()
        context = factory.create(TestDbContext, self.test_options)

        self.assertIsInstance(context, TestDbContext)
        self.assertEqual(context._options, self.test_options)


class TestMongoDbContextIntegration(unittest.TestCase):
    """Integration tests (requires running MongoDB)"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_options: IOptions['test.integration'] = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'test_integration_db',
            'timeout': 5000
        }

    @unittest.skip("Requires running MongoDB instance")
    def test_real_connection(self):
        """Test with real MongoDB connection"""
        with TestDbContext(self.test_options) as context:
            # Create a test collection
            collection = context.get_collection('test_collection')

            # Insert a test document
            result = collection.insert_one({'test': 'data', 'value': 123})
            self.assertIsNotNone(result.inserted_id)

            # Retrieve the document
            document = collection.find_one({'_id': result.inserted_id})
            self.assertEqual(document['test'], 'data')
            self.assertEqual(document['value'], 123)

            # Clean up
            collection.delete_one({'_id': result.inserted_id})

    @unittest.skip("Requires running MongoDB instance")
    def test_multiple_contexts(self):
        """Test using multiple contexts simultaneously"""
        options1: IOptions['test.db1'] = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'test_db1'
        }

        options2: IOptions['test.db2'] = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'test_db2'
        }

        class Context1(MongoDbContext['test.db1']):
            def __init__(self, options: IOptions['test.db1']):
                super().__init__(options)

        class Context2(MongoDbContext['test.db2']):
            def __init__(self, options: IOptions['test.db2']):
                super().__init__(options)

        with Context1(options1) as ctx1, Context2(options2) as ctx2:
            # Both contexts should work independently
            col1 = ctx1.get_collection('test1')
            col2 = ctx2.get_collection('test2')

            col1.insert_one({'db': 'db1'})
            col2.insert_one({'db': 'db2'})

            # Verify isolation
            self.assertIsNotNone(col1.find_one({'db': 'db1'}))
            self.assertIsNotNone(col2.find_one({'db': 'db2'}))


class TestMongoDbContextScenarios(unittest.TestCase):
    """Test various usage scenarios"""

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_minimal_configuration(self, mock_client):
        """Test with minimal required configuration"""
        minimal_options: IOptions['test.minimal'] = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'minimal_db'
        }

        context = TestDbContext(minimal_options)
        _ = context.client

        # Should work with only required fields
        mock_client.assert_called_once_with('mongodb://localhost:27017')

    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_full_configuration(self, mock_client):
        """Test with all configuration options"""
        full_options: IOptions['test.full'] = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'full_db',
            'timeout': 10000,
            'max_pool_size': 200,
            'min_pool_size': 10,
            'server_selection_timeout': 20000
        }

        context = TestDbContext(full_options)
        _ = context.client

        # Should include all options
        mock_client.assert_called_once_with(
            'mongodb://localhost:27017',
            connectTimeoutMS=10000,
            maxPoolSize=200,
            minPoolSize=10,
            serverSelectionTimeoutMS=20000
        )


if __name__ == '__main__':
    unittest.main()
