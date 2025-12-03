"""Remove Service Example

Demonstrates how to remove registered services from the DI container.
Useful for testing, dynamic service replacement, and cleanup scenarios.
"""

import logging

from bclib.context import AppOptions
from bclib.logger import ConsoleLogger, ILogger
from bclib.service_provider import ServiceLifetime, ServiceProvider


# Example services
class ConsoleLogger:
    """Simple console logger"""

    def info(self, message: str):
        print(f"[ConsoleLogger] INFO: {message}")

    def debug(self, message: str):
        print(f"[ConsoleLogger] DEBUG: {message}")


class FileLogger:
    """File logger"""

    def info(self, message: str):
        print(f"[FileLogger] INFO: {message}")

    def debug(self, message: str):
        print(f"[FileLogger] DEBUG: {message}")


class DatabaseService:
    """Database service"""

    def __init__(self, logger):
        self.logger = logger
        self.logger.info("DatabaseService initialized")

    def query(self, sql: str):
        self.logger.debug(f"Executing query: {sql}")
        return []


def example_basic_remove():
    """Basic example of removing a service"""

    services = ServiceProvider()

    print("=" * 60)
    print("Example 1: Basic Service Removal")
    print("=" * 60)

    # Register a service
    services.add_singleton(ConsoleLogger)
    print(f"Registered ConsoleLogger: {services.is_registered(ConsoleLogger)}")

    # Get the service
    logger = services.get_service(ConsoleLogger)
    logger.info("Service is working")

    # Remove the service
    removed = services.remove_service(ConsoleLogger)
    print(f"Service removed: {removed}")
    print(f"Still registered: {services.is_registered(ConsoleLogger)}")

    # Try to get after removal
    logger = services.get_service(ConsoleLogger)
    print(f"Service after removal: {logger}")

    # Try to remove again
    removed_again = services.remove_service(ConsoleLogger)
    print(f"Remove again result: {removed_again}")

    print("\n✓ Basic removal working!\n")


def example_replace_service():
    """Example of replacing a service by removing and re-registering"""

    services = ServiceProvider()

    print("=" * 60)
    print("Example 2: Replace Service")
    print("=" * 60)

    # Register initial logger
    services.add_singleton(ConsoleLogger)
    logger1 = services.get_service(ConsoleLogger)
    logger1.info("Using ConsoleLogger")

    # Replace with FileLogger
    print("\nReplacing ConsoleLogger with FileLogger...")
    services.remove_service(ConsoleLogger)
    # Register FileLogger as ConsoleLogger
    services.add_singleton(ConsoleLogger, FileLogger)

    logger2 = services.get_service(ConsoleLogger)
    logger2.info("Using FileLogger now")

    print("\n✓ Service replacement working!\n")


def example_remove_with_dependencies():
    """Example showing removal of service with dependencies"""

    services = ServiceProvider()

    print("=" * 60)
    print("Example 3: Remove Service with Dependencies")
    print("=" * 60)

    # Register logger and database
    services.add_singleton(ConsoleLogger)
    services.add_transient(DatabaseService)

    # Create database (depends on logger)
    db = services.get_service(DatabaseService)
    db.query("SELECT * FROM users")

    print(f"\nLogger registered: {services.is_registered(ConsoleLogger)}")
    print(f"Database registered: {services.is_registered(DatabaseService)}")

    # Remove database service
    print("\nRemoving DatabaseService...")
    services.remove_service(DatabaseService)
    print(f"Database registered: {services.is_registered(DatabaseService)}")
    print(f"Logger still registered: {services.is_registered(ConsoleLogger)}")

    # Logger still works
    logger = services.get_service(ConsoleLogger)
    logger.info("Logger still working after database removal")

    print("\n✓ Dependency removal working!\n")


def example_scoped_removal():
    """Example of removing scoped services"""

    services = ServiceProvider()

    print("=" * 60)
    print("Example 4: Remove Scoped Service")
    print("=" * 60)

    # Register scoped service
    services.add_scoped(DatabaseService)
    services.add_singleton(ConsoleLogger)

    # Create scoped instance
    db1 = services.get_service(DatabaseService)
    print(f"Created scoped instance: {db1 is not None}")

    # Same instance in same scope
    db2 = services.get_service(DatabaseService)
    print(f"Same instance: {db1 is db2}")

    # Remove the service
    print("\nRemoving scoped service...")
    removed = services.remove_service(DatabaseService)
    print(f"Service removed: {removed}")
    print(f"Registered: {services.is_registered(DatabaseService)}")

    # Try to get after removal
    db3 = services.get_service(DatabaseService)
    print(f"Service after removal: {db3}")

    print("\n✓ Scoped service removal working!\n")


def example_test_cleanup():
    """Example of using remove for test cleanup"""

    print("=" * 60)
    print("Example 5: Test Cleanup Pattern")
    print("=" * 60)

    def setup_test_services():
        """Setup services for testing"""
        services = ServiceProvider()
        services.add_singleton(ConsoleLogger)
        services.add_transient(DatabaseService)
        return services

    def cleanup_test_services(services: ServiceProvider):
        """Cleanup test services"""
        services.remove_service(DatabaseService)
        services.remove_service(ConsoleLogger)

    # Test 1
    print("\nTest 1: Running with services")
    services = setup_test_services()
    db = services.get_service(DatabaseService)
    db.query("SELECT * FROM test1")
    print(
        f"Services registered: Logger={services.is_registered(ConsoleLogger)}, DB={services.is_registered(DatabaseService)}")

    cleanup_test_services(services)
    print(
        f"After cleanup: Logger={services.is_registered(ConsoleLogger)}, DB={services.is_registered(DatabaseService)}")

    # Test 2 - fresh setup
    print("\nTest 2: Fresh setup after cleanup")
    services = setup_test_services()
    db = services.get_service(DatabaseService)
    db.query("SELECT * FROM test2")
    print(
        f"Services registered: Logger={services.is_registered(ConsoleLogger)}, DB={services.is_registered(DatabaseService)}")

    cleanup_test_services(services)

    print("\n✓ Test cleanup pattern working!\n")


def example_dynamic_reconfiguration():
    """Example of dynamic service reconfiguration"""

    services = ServiceProvider()

    print("=" * 60)
    print("Example 6: Dynamic Reconfiguration")
    print("=" * 60)

    # Initial configuration - development
    print("\nDevelopment configuration:")
    services.add_singleton(ConsoleLogger)
    logger = services.get_service(ConsoleLogger)
    logger.info("Development mode - console logging")
    print(f"Lifetime: {services.get_lifetime(ConsoleLogger)}")

    # Switch to production configuration
    print("\nSwitching to production configuration...")
    services.remove_service(ConsoleLogger)
    services.add_singleton(ConsoleLogger, FileLogger)

    logger = services.get_service(ConsoleLogger)
    logger.info("Production mode - file logging")
    print(f"Lifetime: {services.get_lifetime(ConsoleLogger)}")

    print("\n✓ Dynamic reconfiguration working!\n")


def example_ilogger_removal():
    """Example of removing ILogger service"""

    services = ServiceProvider()

    print("=" * 60)
    print("Example 7: Remove ILogger Service")
    print("=" * 60)

    # Register ILogger with factory
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        return ConsoleLogger.create_logger("Example", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)

    # Use logger
    logger = services.get_service(ILogger)
    if logger:
        logger.info("Logger is working")

    print(f"ILogger registered: {services.is_registered(ILogger)}")
    print(f"ILogger lifetime: {services.get_lifetime(ILogger)}")

    # Remove logger
    print("\nRemoving ILogger...")
    removed = services.remove_service(ILogger)
    print(f"Removed: {removed}")
    print(f"Still registered: {services.is_registered(ILogger)}")

    # Register new logger with different config
    print("\nRegistering new logger with DEBUG level...")
    logger_options.log_level = logging.DEBUG
    services.add_singleton(ILogger, factory=logger_factory)

    logger = services.get_service(ILogger)
    if logger:
        logger.debug("New logger with DEBUG level")

    print("\n✓ ILogger removal and replacement working!\n")


if __name__ == "__main__":
    example_basic_remove()
    example_replace_service()
    example_remove_with_dependencies()
    example_scoped_removal()
    example_test_cleanup()
    example_dynamic_reconfiguration()
    example_ilogger_removal()

    print("=" * 60)
    print("All service removal examples completed!")
    print("=" * 60)
