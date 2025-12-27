"""Debug get_service for IOptions"""
import sys
from typing import get_args, get_origin

from bclib.di import ServiceProvider, extract_generic_type_key
from bclib.options import IOptions

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


config = {
    "database": {
        "host": "localhost",
        "port": 5432
    }
}

sp = ServiceProvider()


def create_options(sp, **kwargs):
    """Factory for creating IOptions with configuration key"""
    key = extract_generic_type_key(kwargs)
    return IOptions(key, config)


sp.add_singleton(IOptions, factory=create_options)

print("=== Testing get_service with IOptions ===\n")

# Test 1: Direct generic type
print("Test 1: IOptions['database']")
service_type = IOptions['database']
print(f"  Type: {service_type}")
print(f"  Origin: {get_origin(service_type)}")
print(f"  Args: {get_args(service_type)}")

result = sp.get_service(service_type)
print(f"  Result: {result}")
print(f"  Result value: {result.value if result else 'None'}")
print()

# Test 2: Base type
print("Test 2: IOptions (base type)")
result2 = sp.get_service(IOptions)
print(f"  Result: {result2}")
print(f"  Result value: {result2.value if result2 else 'None'}")
print()

# Test 3: Check descriptors
print("Test 3: ServiceProvider descriptors")
print(f"  Registered types: {list(sp._descriptors.keys())}")
print(f"  IOptions in descriptors: {IOptions in sp._descriptors}")
print(
    f"  get_origin(IOptions['database']) in descriptors: {get_origin(IOptions['database']) in sp._descriptors}")
