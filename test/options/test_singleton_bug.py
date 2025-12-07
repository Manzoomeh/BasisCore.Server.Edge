"""Test to reproduce singleton bug with IOptions['key']"""

from bclib.options import AppOptions, IOptions, add_options_service
from bclib.service_provider import ServiceProvider


def test_singleton_registration():
    """
    Test: Register IOptions as singleton using add_options_service
    Should create different instances for different generic type arguments
    """
    print("=== Testing Singleton Registration ===\n")

    config = {
        "test": {"value": "test_config"},
        "test1": {"value": "test1_config"}
    }

    sp = ServiceProvider()

    # Register AppOptions and IOptions properly
    sp.add_singleton(AppOptions, instance=config)
    sp.add_singleton(IOptions, factory=lambda sp, **
                     kwargs: _create_options(sp, **kwargs))

    print("Resolving IOptions['test']...")
    options_test = sp.get_service(IOptions['test'])
    print(f"  IOptions['test'] content: {dict(options_test)}")
    print(f"  IOptions['test'] id: {id(options_test)}")

    print("\nResolving IOptions['test1']...")
    options_test1 = sp.get_service(IOptions['test1'])
    print(f"  IOptions['test1'] content: {dict(options_test1)}")
    print(f"  IOptions['test1'] id: {id(options_test1)}")

    # Resolve same key again - should return cached singleton
    print("\nResolving IOptions['test'] again...")
    options_test_again = sp.get_service(IOptions['test'])
    print(f"  IOptions['test'] id: {id(options_test_again)}")
    print(f"  Is same instance as first? {options_test is options_test_again}")

    # Summary
    print("\n--- Results ---")
    print(
        f"Different instances for different keys? {options_test is not options_test1}")
    print(
        f"Different content for different keys? {dict(options_test) != dict(options_test1)}")
    print(
        f"Same instance when resolving same key? {options_test is options_test_again}")

    if options_test is options_test1:
        print("\n❌ BUG: Singleton returns same instance for different generic types!")
    elif dict(options_test) == dict(options_test1):
        print("\n❌ BUG: Different instances but same content!")
    elif options_test is not options_test_again:
        print("\n❌ BUG: Singleton should return same instance for same generic type!")
    else:
        print("\n✅ All checks passed!")


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


def test_transient_registration():
    """
    Test: Register IOptions as transient
    Should create different instances every time
    """
    print("\n\n=== Testing Transient Registration ===\n")

    config = {
        "test": {"value": "test_config"},
        "test1": {"value": "test1_config"}
    }

    sp = ServiceProvider()
    add_options_service(sp, config)  # Uses transient by default

    print("Resolving IOptions['test']...")
    options_test = sp.get_service(IOptions['test'])
    print(f"  IOptions['test'] content: {dict(options_test)}")
    print(f"  IOptions['test'] id: {id(options_test)}")

    print("\nResolving IOptions['test1']...")
    options_test1 = sp.get_service(IOptions['test1'])
    print(f"  IOptions['test1'] content: {dict(options_test1)}")
    print(f"  IOptions['test1'] id: {id(options_test1)}")

    # Resolve same key again - should create new instance (transient)
    print("\nResolving IOptions['test'] again...")
    options_test_again = sp.get_service(IOptions['test'])
    print(f"  IOptions['test'] id: {id(options_test_again)}")
    print(f"  Is same instance as first? {options_test is options_test_again}")

    # Summary
    print("\n--- Results ---")
    print(
        f"Different instances for different keys? {options_test is not options_test1}")
    print(
        f"Different content for different keys? {dict(options_test) != dict(options_test1)}")
    print(
        f"New instance when resolving same key? {options_test is not options_test_again}")

    if dict(options_test) != dict(options_test1):
        print("\n✅ Transient creates correct instances with different content!")
    else:
        print("\n❌ BUG: Same content for different keys!")


if __name__ == "__main__":
    test_singleton_registration()
    test_transient_registration()
