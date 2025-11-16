"""
Unit Test - Factory with ServiceProvider Parameter

Tests the new factory signature that receives ServiceProvider.
This allows factories to resolve other services from the DI container.
"""
import unittest

from bclib.service_provider import ServiceProvider


# Interfaces
class ILogger:
    def log(self, message: str): ...


class IConfig:
    def get(self, key: str) -> str: ...


class IDatabase:
    def connect(self) -> str: ...


# Implementations
class ConsoleLogger(ILogger):
    def __init__(self):
        self.messages = []
    
    def log(self, message: str):
        self.messages.append(message)


class AppConfig(IConfig):
    def __init__(self):
        self.settings = {
            "db_host": "localhost",
            "db_port": "5432",
            "db_name": "testdb"
        }
    
    def get(self, key: str) -> str:
        return self.settings.get(key, "")


class PostgresDatabase(IDatabase):
    """Database that depends on Logger and Config"""
    
    def __init__(self, logger: ILogger, config: IConfig):
        self.logger = logger
        self.config = config
        self.logger.log("PostgresDatabase created with dependencies!")
    
    def connect(self) -> str:
        host = self.config.get("db_host")
        port = self.config.get("db_port")
        db_name = self.config.get("db_name")
        connection_string = f"postgresql://{host}:{port}/{db_name}"
        self.logger.log(f"Connecting to: {connection_string}")
        return connection_string


class TestFactoryWithServiceProvider(unittest.TestCase):
    """Test factory functions receiving ServiceProvider parameter"""
    
    def test_factory_receives_service_provider(self):
        """Test that factory receives ServiceProvider and can resolve dependencies"""
        services = ServiceProvider()
        
        # Register services with factories that receive ServiceProvider
        services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
        services.add_singleton(IConfig, factory=lambda sp: AppConfig())
        services.add_singleton(
            IDatabase,
            factory=lambda sp: PostgresDatabase(
                sp.get_service(ILogger),
                sp.get_service(IConfig)
            )
        )
        
        # Resolve database - should automatically resolve its dependencies
        db = services.get_service(IDatabase)
        
        # Verify database was created
        self.assertIsInstance(db, PostgresDatabase)
        
        # Verify logger was injected and used
        logger = services.get_service(ILogger)
        self.assertIn("PostgresDatabase created with dependencies!", logger.messages)
        
        # Test database connection
        connection_string = db.connect()
        self.assertEqual(connection_string, "postgresql://localhost:5432/testdb")
        self.assertIn("Connecting to: postgresql://localhost:5432/testdb", logger.messages)
    
    def test_factory_with_multiple_dependencies(self):
        """Test factory resolving multiple dependencies"""
        services = ServiceProvider()
        
        services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
        services.add_singleton(IConfig, factory=lambda sp: AppConfig())
        
        # Complex factory with multiple dependencies
        services.add_singleton(
            IDatabase,
            factory=lambda sp: PostgresDatabase(
                logger=sp.get_service(ILogger),
                config=sp.get_service(IConfig)
            )
        )
        
        db = services.get_service(IDatabase)
        logger = services.get_service(ILogger)
        
        # Verify all dependencies were resolved
        self.assertIsNotNone(db.logger)
        self.assertIsNotNone(db.config)
        self.assertIsInstance(db.logger, ConsoleLogger)
        self.assertIsInstance(db.config, AppConfig)
        
        # Verify same logger instance
        self.assertIs(db.logger, logger)
    
    def test_factory_with_scoped_lifetime(self):
        """Test factory with scoped lifetime"""
        services = ServiceProvider()
        
        services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
        services.add_scoped(IConfig, factory=lambda sp: AppConfig())
        services.add_scoped(
            IDatabase,
            factory=lambda sp: PostgresDatabase(
                sp.get_service(ILogger),
                sp.get_service(IConfig)
            )
        )
        
        # Create scope
        scope = services.create_scope()
        
        # Get database from scope
        db1 = scope.get_service(IDatabase)
        db2 = scope.get_service(IDatabase)
        
        # Scoped services should be same instance within scope
        self.assertIs(db1, db2)
        
        # But different from another scope
        scope2 = services.create_scope()
        db3 = scope2.get_service(IDatabase)
        self.assertIsNot(db1, db3)
    
    def test_factory_with_transient_lifetime(self):
        """Test factory with transient lifetime"""
        services = ServiceProvider()
        
        services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
        services.add_transient(
            IConfig,
            factory=lambda sp: AppConfig()
        )
        
        # Get multiple instances
        config1 = services.get_service(IConfig)
        config2 = services.get_service(IConfig)
        
        # Transient services should be different instances
        self.assertIsNot(config1, config2)
        self.assertIsInstance(config1, AppConfig)
        self.assertIsInstance(config2, AppConfig)


def run_tests():
    """Run all tests and display results"""
    print("=" * 70)
    print("Factory with ServiceProvider - Unit Tests")
    print("=" * 70)
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFactoryWithServiceProvider)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print()
        print("Key Feature Demonstrated:")
        print("  - Factory functions now receive ServiceProvider parameter")
        print("  - Factories can resolve dependencies: sp.get_service(ILogger)")
        print("  - Works with all lifetimes: singleton, scoped, transient")
        print()
        print("Example:")
        print("  services.add_singleton(")
        print("      IDatabase,")
        print("      factory=lambda sp: PostgresDatabase(")
        print("          sp.get_service(ILogger),")
        print("          sp.get_service(IConfig)")
        print("      )")
        print("  )")
    else:
        print("✗ Some tests failed")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
