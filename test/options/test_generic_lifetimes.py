"""Comprehensive test for generic singleton/scoped services"""

from bclib.options import AppOptions, IOptions, add_options_service
from bclib.di import ServiceProvider


def test_generic_singleton_caching():
    """
    Test that generic singletons are cached correctly per generic type argument
    """
    print("=== Test: Generic Singleton Caching ===\n")

    config = {
        "logger1": {"level": "DEBUG"},
        "logger2": {"level": "INFO"},
        "logger3": {"level": "ERROR"}
    }

    sp = ServiceProvider()
    sp.add_singleton(AppOptions, instance=config)
    sp.add_singleton(IOptions, factory=lambda sp, **
                     kwargs: _create_options(sp, **kwargs))

    # Request same key multiple times - should return same instance
    log1_a = sp.get_service(IOptions['logger1'])
    log1_b = sp.get_service(IOptions['logger1'])
    log1_c = sp.get_service(IOptions['logger1'])

    print(f"IOptions['logger1'] - First:  {id(log1_a)}")
    print(f"IOptions['logger1'] - Second: {id(log1_b)}")
    print(f"IOptions['logger1'] - Third:  {id(log1_c)}")
    print(f"All same instance? {log1_a is log1_b is log1_c}")

    # Request different keys - should return different instances
    log2 = sp.get_service(IOptions['logger2'])
    log3 = sp.get_service(IOptions['logger3'])

    print(f"\nIOptions['logger2']: {id(log2)}")
    print(f"IOptions['logger3']: {id(log3)}")
    print(
        f"All different? {log1_a is not log2 and log2 is not log3 and log1_a is not log3}")

    # Verify content
    print(f"\nContent verification:")
    print(f"  logger1: {dict(log1_a)}")
    print(f"  logger2: {dict(log2)}")
    print(f"  logger3: {dict(log3)}")

    success = (
        log1_a is log1_b is log1_c and  # Same key returns same instance
        log1_a is not log2 and  # Different keys return different instances
        log2 is not log3 and
        dict(log1_a) == {"level": "DEBUG"} and  # Correct content
        dict(log2) == {"level": "INFO"} and
        dict(log3) == {"level": "ERROR"}
    )

    print(f"\n{'✅' if success else '❌'} Generic singleton caching {'works' if success else 'failed'}!\n")
    return success


def test_generic_scoped_caching():
    """
    Test that generic scoped services are cached correctly per scope
    """
    print("=== Test: Generic Scoped Service Caching ===\n")

    config = {
        "db1": {"host": "primary.db"},
        "db2": {"host": "secondary.db"}
    }

    sp = ServiceProvider()
    sp.add_singleton(AppOptions, instance=config)
    sp.add_scoped(IOptions, factory=lambda sp, **
                  kwargs: _create_options(sp, **kwargs))

    # First scope
    print("Scope 1:")
    db1_scope1_a = sp.get_service(IOptions['db1'])
    db1_scope1_b = sp.get_service(IOptions['db1'])
    db2_scope1 = sp.get_service(IOptions['db2'])

    print(f"  IOptions['db1'] first:  {id(db1_scope1_a)}")
    print(f"  IOptions['db1'] second: {id(db1_scope1_b)}")
    print(f"  Same instance in scope? {db1_scope1_a is db1_scope1_b}")
    print(f"  IOptions['db2']: {id(db2_scope1)}")
    print(f"  Different from db1? {db1_scope1_a is not db2_scope1}")

    # Create new scope
    sp2 = sp.create_scope()
    print("\nScope 2:")
    db1_scope2 = sp2.get_service(IOptions['db1'])
    db2_scope2 = sp2.get_service(IOptions['db2'])

    print(f"  IOptions['db1']: {id(db1_scope2)}")
    print(f"  IOptions['db2']: {id(db2_scope2)}")
    print(
        f"  Different from scope 1? db1: {db1_scope1_a is not db1_scope2}, db2: {db2_scope1 is not db2_scope2}")

    success = (
        db1_scope1_a is db1_scope1_b and  # Same key in same scope = same instance
        db1_scope1_a is not db2_scope1 and  # Different keys = different instances
        db1_scope1_a is not db1_scope2  # Different scopes = different instances
    )

    print(f"\n{'✅' if success else '❌'} Generic scoped caching {'works' if success else 'failed'}!\n")
    return success


def test_generic_transient():
    """
    Test that generic transient services always create new instances
    """
    print("=== Test: Generic Transient Services ===\n")

    config = {
        "temp": {"id": "temp123"}
    }

    sp = ServiceProvider()
    add_options_service(sp, config)  # Uses transient

    temp1 = sp.get_service(IOptions['temp'])
    temp2 = sp.get_service(IOptions['temp'])
    temp3 = sp.get_service(IOptions['temp'])

    print(f"IOptions['temp'] - First:  {id(temp1)}")
    print(f"IOptions['temp'] - Second: {id(temp2)}")
    print(f"IOptions['temp'] - Third:  {id(temp3)}")

    success = temp1 is not temp2 and temp2 is not temp3 and temp1 is not temp3

    print(f"\nAll different instances? {success}")
    print(f"But same content? {dict(temp1) == dict(temp2) == dict(temp3)}")

    print(f"\n{'✅' if success else '❌'} Generic transient {'works' if success else 'failed'}!\n")
    return success


def _create_options(sp, **kwargs):
    """Factory for creating Options with configuration key"""
    from typing import ForwardRef

    from bclib.options.service_options import ServiceOptions

    app_options = sp.get_service(AppOptions)
    type_args = kwargs.get('generic_type_args', ('',))

    # Extract key from generic type argument
    key_source = type_args[0]
    if isinstance(key_source, ForwardRef):
        key = key_source.__forward_arg__
    elif isinstance(key_source, type):
        key = key_source.__name__
    elif isinstance(key_source, str):
        key = key_source
    else:
        key = str(key_source)

    return ServiceOptions(key, app_options)


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "Generic Service Lifetime Tests")
    print("="*70 + "\n")

    results = []
    results.append(test_generic_singleton_caching())
    results.append(test_generic_scoped_caching())
    results.append(test_generic_transient())

    print("="*70)
    if all(results):
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)
