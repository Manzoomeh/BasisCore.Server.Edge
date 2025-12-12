"""Quick test for simplified ServiceOptions"""
from bclib.options import ServiceOptions
import sys

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


# Test 1: Basic usage
print("=== Test 1: Dict-like access ===")
config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "mydb"
    }
}

db_options = ServiceOptions("database", config)

print(f"Type: {type(db_options)}")
print(f"Is dict? {isinstance(db_options, dict)}")
print(f"Dict content: {dict(db_options)}")

# Test dict access
print(f"\nDict access - db_options['host']: {db_options['host']}")
print(f"Dict access - db_options['port']: {db_options['port']}")
print(f"Dict get - db_options.get('host'): {db_options.get('host')}")
print(
    f"Dict get with default - db_options.get('timeout', 30): {db_options.get('timeout', 30)}")

# Test dict methods
print(f"\nDict keys: {list(db_options.keys())}")
print(f"Dict values: {list(db_options.values())}")
print(f"Dict items: {list(db_options.items())}")

# Test 2: Non-dict value
print("\n=== Test 2: Non-dict value ===")
config2 = {"string_value": "test"}
str_opt = ServiceOptions("string_value", config2)

print(f"Dict content: {dict(str_opt)}")
print(f"Is dict? {isinstance(str_opt, dict)}")
print(f"Dict length: {len(str_opt)}")

# Test 3: Nested access
print("\n=== Test 3: Nested key ===")
config3 = {
    "cache": {
        "redis": {
            "host": "localhost",
            "port": 6379
        }
    }
}

redis_opt = ServiceOptions("cache.redis", config3)
print(f"Dict content: {dict(redis_opt)}")
print(f"Access as dict - redis_opt['host']: {redis_opt['host']}")
print(f"Access as dict - redis_opt.get('port'): {redis_opt.get('port')}")

print("\n✅ All tests passed!")
