"""Test IOptions - Configuration access via dependency injection"""
import asyncio

from bclib import edge
from bclib.options import IOptions


class DatabaseService:
    """Service that needs database configuration"""

    def __init__(self, db_options: IOptions['database']):
        """
        Initialize with database configuration

        Args:
            db_options: Database configuration from AppOptions
        """
        self.db_config = db_options.value
        self.db_options = db_options

    def connect(self):
        """Simulate database connection using config"""
        print(f"Connecting to database: {self.db_config}")
        print(f"  Host: {self.db_options.get('host', 'localhost')}")
        print(f"  Port: {self.db_options.get('port', 5432)}")
        print(f"  Database: {self.db_options.get('database', 'mydb')}")


class CacheService:
    """Service that needs cache configuration"""

    def __init__(self, cache_options: IOptions['cache.redis']):
        """
        Initialize with Redis cache configuration

        Args:
            cache_options: Redis cache configuration from AppOptions['cache']['redis']
        """
        self.cache_config = cache_options.value
        self.cache_options = cache_options

    def connect(self):
        """Simulate cache connection using config"""
        print(f"Connecting to Redis cache: {self.cache_config}")
        print(f"  Host: {self.cache_options.get('host', 'localhost')}")
        print(f"  Port: {self.cache_options.get('port', 6379)}")


class ConfigMonitor:
    """Service that needs access to entire configuration"""

    def __init__(self, all_options: IOptions['root']):
        """
        Initialize with all configuration

        Args:
            all_options: All application configuration
        """
        self.config = all_options.value
        self.options = all_options

    def show_config(self):
        """Display configuration summary"""
        print(f"All configuration keys: {list(self.config.keys())}")
        print(f"Full config: {self.config}")


@edge.restful_handler("GET", "/test-options")
async def test_options_handler(
    db_service: DatabaseService,
    cache_service: CacheService,
    monitor: ConfigMonitor
):
    """Test endpoint to verify IOptions injection"""
    print("\n=== Testing IOptions Injection ===\n")

    print("1. Database Service:")
    db_service.connect()

    print("\n2. Cache Service:")
    cache_service.connect()

    print("\n3. Config Monitor:")
    monitor.show_config()

    return {
        "status": "success",
        "message": "IOptions injection working correctly",
        "database_config": db_service.db_config,
        "cache_config": cache_service.cache_config,
        "all_config_keys": list(monitor.config.keys())
    }


if __name__ == "__main__":
    # Test configuration
    options = {
        "http": "localhost:8080",
        "database": {
            "host": "db.example.com",
            "port": 5432,
            "database": "production_db",
            "user": "admin",
            "password": "secret"
        },
        "cache": {
            "redis": {
                "host": "redis.example.com",
                "port": 6379,
                "db": 0
            },
            "memcached": {
                "host": "memcached.example.com",
                "port": 11211
            }
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        }
    }

    print("Starting server with IOptions test...")
    print("Visit: http://localhost:8080/test-options")
    print("\nPress Ctrl+C to stop\n")

    dispatcher = edge.from_options(options)
    dispatcher.routing_table.print()

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        loop.close()
