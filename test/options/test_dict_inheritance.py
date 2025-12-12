"""Comprehensive test for ServiceOptions with dict inheritance"""
from bclib.di import ServiceProvider
from bclib.options import ServiceOptions, add_options_service
import sys

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


def test_dict_behavior():
    """Test that ServiceOptions behaves like a dict"""
    print("=== Test 1: Dict Behavior ===\n")

    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "mydb",
            "timeout": 30
        }
    }

    db_options = ServiceOptions("database", config)

    # Test isinstance
    assert isinstance(db_options, dict), "Should be instance of dict"
    print("✓ isinstance(db_options, dict) = True")

    # Test dict access
    assert db_options['host'] == 'localhost', "Dict access failed"
    print("✓ db_options['host'] = 'localhost'")

    # Test get method
    assert db_options.get('port') == 5432, "get() method failed"
    print("✓ db_options.get('port') = 5432")

    # Test get with default
    assert db_options.get(
        'missing', 'default') == 'default', "get() with default failed"
    print("✓ db_options.get('missing', 'default') = 'default'")

    # Test keys()
    keys = list(db_options.keys())
    assert 'host' in keys, "keys() method failed"
    print(f"✓ db_options.keys() = {keys}")

    # Test values()
    values = list(db_options.values())
    assert 'localhost' in values, "values() method failed"
    print(f"✓ db_options.values() contains 'localhost'")

    # Test items()
    items = dict(db_options.items())
    assert items['host'] == 'localhost', "items() method failed"
    print("✓ db_options.items() works correctly")

    # Test len()
    assert len(db_options) == 4, "len() failed"
    print(f"✓ len(db_options) = {len(db_options)}")

    # Test 'in' operator
    assert 'host' in db_options, "'in' operator failed"
    print("✓ 'host' in db_options = True")

    # Test iteration
    for key in db_options:
        assert key in ['host', 'port', 'name', 'timeout'], "Iteration failed"
    print("✓ Iteration works correctly")

    print("\n✅ All dict behavior tests passed!\n")


def test_property_access():
    """Test value and key properties"""
    print("=== Test 2: Property Access ===\n")

    config = {
        "cache": {
            "redis": {
                "host": "redis.local",
                "port": 6379
            }
        }
    }

    redis_opt = ServiceOptions("cache.redis", config)

    # Test dict content
    expected_dict = {"host": "redis.local", "port": 6379}
    assert dict(redis_opt) == expected_dict, "dict content failed"
    print(f"✓ dict(redis_opt) = {dict(redis_opt)}")

    # Removed key property test (no longer exists)

    # Test that dict access is working
    assert redis_opt['host'] == expected_dict['host'], "Dict access failed"
    print("✓ Dict access working correctly")

    print("\n✅ All property access tests passed!\n")


def test_with_di_container():
    """Test ServiceOptions with DI container"""
    print("=== Test 3: DI Container Integration ===\n")

    config = {
        "database": {
            "host": "db.example.com",
            "port": 5432,
            "database": "production"
        },
        "cache": {
            "host": "cache.example.com",
            "port": 6379
        }
    }

    sp = ServiceProvider()
    add_options_service(sp, config)

    # Define service that uses IOptions
    from bclib.options import IOptions

    class DatabaseService:
        def __init__(self, db_config: IOptions['database']):
            self.config = db_config

    sp.add_transient(DatabaseService)

    # Get service and verify
    db_service = sp.get_service(DatabaseService)

    # Test that injected config is a dict
    assert isinstance(db_service.config,
                      dict), "Injected config should be dict"
    print("✓ Injected config is instance of dict")

    # Test dict access on injected config
    assert db_service.config['host'] == 'db.example.com', "Dict access on injected config failed"
    print(f"✓ db_service.config['host'] = '{db_service.config['host']}'")

    # Test dict content
    assert db_service.config['port'] == 5432, "dict port access failed"
    print(f"✓ db_service.config['port'] = {db_service.config['port']}")

    # Removed key property test (no longer exists)

    print("\n✅ All DI integration tests passed!\n")


def test_non_dict_values():
    """Test ServiceOptions with non-dict values (now only dict values are supported)"""
    print("=== Test 4: Non-Dict Values ===\n")

    # Note: After removing .value property, ServiceOptions only supports dict values
    # Non-dict config values should be accessed directly from AppOptions

    config = {
        "nested": {
            "setting": "value123"
        },
        "port": 8080
    }

    # Test nested dict value
    nested_opt = ServiceOptions("nested", config)
    assert nested_opt['setting'] == "value123", "Nested dict access failed"
    print(f"✓ Nested dict value: {dict(nested_opt)}")

    # For non-dict values, they initialize as empty dict now
    # This is expected behavior since dict inheritance requires dict values
    port_opt = ServiceOptions("port", config)
    assert len(port_opt) == 0, "Non-dict should result in empty dict"
    print(f"✓ Non-dict value results in empty dict: len={len(port_opt)}")

    print("\n✅ All dict value tests passed!\n")


def test_repr():
    """Test string representation (now uses dict's default repr)"""
    print("=== Test 5: String Representation ===\n")

    config = {"db": {"host": "localhost"}}
    opt = ServiceOptions("db", config)

    repr_str = repr(opt)
    # After simplification, uses dict's default repr
    assert "host" in repr_str and "localhost" in repr_str, "repr should show dict content"
    print(f"✓ repr(opt) = {repr_str}")

    print("\n✅ String representation test passed!\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "ServiceOptions Dict Inheritance Tests")
    print("="*70 + "\n")

    try:
        test_dict_behavior()
        test_property_access()
        test_with_di_container()
        test_non_dict_values()
        test_repr()

        print("="*70)
        print(" " * 20 + "✅ All Tests Passed!")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
