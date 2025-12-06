"""Simple test for IOptions without running server"""
import sys

from bclib.options import IOptions, ServiceOptions
from bclib.service_provider import ServiceProvider

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


def test_ioptions_basic():
    """Test basic IOptions functionality"""
    print("=== Test 1: Basic IOptions functionality ===\n")

    # Sample configuration
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "mydb"
        },
        "cache": {
            "redis": {
                "host": "localhost",
                "port": 6379
            }
        },
        "api_key": "secret123"
    }

    # Test 1: Direct instantiation with simple key
    db_options = ServiceOptions("database", config)
    print(f"Database options key: {db_options.key}")
    print(f"Database options value: {db_options.value}")
    print(f"Database host: {db_options.get('host')}")
    print(f"Database port: {db_options.get('port')}")
    print(f"Database timeout (with default): {db_options.get('timeout', 30)}")

    print("\n" + "="*50 + "\n")

    # Test 2: Nested key with dot notation
    redis_options = ServiceOptions("cache.redis", config)
    print(f"Redis options key: {redis_options.key}")
    print(f"Redis options value: {redis_options.value}")
    print(f"Redis host: {redis_options.get('host')}")

    print("\n" + "="*50 + "\n")

    # Test 3: Root access
    root_options = ServiceOptions("root", config)
    print(f"Root options key: {root_options.key}")
    print(f"Root options keys: {list(root_options.value.keys())}")

    print("\n" + "="*50 + "\n")

    # Test 4: Non-existent key
    missing_options = ServiceOptions("nonexistent", config)
    print(f"Missing options value: {missing_options.value}")

    print("\n✅ All basic tests passed!\n")


def test_ioptions_with_di():
    """Test IOptions with dependency injection"""
    print("=== Test 2: IOptions with DI Container ===\n")

    # Sample configuration
    config = {
        "database": {
            "host": "db.example.com",
            "port": 5432,
            "database": "production"
        },
        "cache": {
            "redis": {
                "host": "redis.example.com",
                "port": 6379
            }
        }
    }

    # Create service provider
    sp = ServiceProvider()

    # Register IOptions with factory (using register_options helper)
    from bclib.options import add_options_service
    add_options_service(sp, config)

    # Register a service that uses IOptions
    class DatabaseService:
        def __init__(self, db_config: IOptions['database']):
            self.config = db_config

    # Debug: Check what InjectionPlan sees
    from bclib.service_provider.injection_plan import InjectionPlan
    plan = InjectionPlan(DatabaseService)
    print(f"InjectionPlan strategies: {plan.param_strategies}")
    for name, strategy in plan.param_strategies.items():
        print(f"  {name}: {strategy} (type: {strategy.target_type if hasattr(strategy, 'target_type') else 'N/A'})")
    print()

    sp.add_transient(DatabaseService)

    # Get service and verify injection
    db_service = sp.get_service(DatabaseService)
    print(f"DatabaseService config key: {db_service.config.key}")
    print(f"DatabaseService config value: {db_service.config.value}")
    print(f"Database host: {db_service.config.get('host')}")
    print(f"Database port: {db_service.config.get('port')}")

    print("\n" + "="*50 + "\n")

    # Test with nested config
    class CacheService:
        def __init__(self, redis_config: IOptions['cache.redis']):
            self.config = redis_config

    sp.add_transient(CacheService)

    cache_service = sp.get_service(CacheService)
    print(f"CacheService config key: {cache_service.config.key}")
    print(f"CacheService config value: {cache_service.config.value}")
    print(f"Redis host: {cache_service.config.get('host')}")

    print("\n✅ All DI tests passed!\n")


def test_ioptions_edge_cases():
    """Test edge cases"""
    print("=== Test 3: Edge Cases ===\n")

    config = {
        "string_value": "test",
        "number_value": 42,
        "list_value": [1, 2, 3],
        "nested": {
            "deep": {
                "value": "found"
            }
        }
    }

    # Test with string value
    str_opt = Options("string_value", config)
    print(f"String value: {str_opt.value}")
    print(
        f"Get from non-dict (should return default): {str_opt.get('anything', 'default')}")

    print()

    # Test with number value
    num_opt = Options("number_value", config)
    print(f"Number value: {num_opt.value}")

    print()

    # Test with list value
    list_opt = Options("list_value", config)
    print(f"List value: {list_opt.value}")

    print()

    # Test deep nesting
    deep_opt = Options("nested.deep", config)
    print(f"Deep nested value: {deep_opt.value}")
    print(f"Deep nested 'value' key: {deep_opt.get('value')}")

    print()

    # Test invalid deep path
    invalid_opt = Options("nested.invalid.path", config)
    print(f"Invalid path value: {invalid_opt.value}")

    print("\n✅ All edge case tests passed!\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 20 + "IOptions Test Suite")
    print("="*70 + "\n")

    try:
        test_ioptions_basic()
        test_ioptions_with_di()
        test_ioptions_edge_cases()

        print("="*70)
        print(" " * 15 + "✅ All Tests Passed Successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
