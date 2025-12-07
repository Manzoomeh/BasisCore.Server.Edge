"""Simple test to debug IOptions content"""

from bclib.options import AppOptions, IOptions, add_options_service
from bclib.service_provider import ServiceProvider


def test_direct_creation():
    """Test ServiceOptions directly"""
    print("=== Test 1: Direct ServiceOptions Creation ===\n")

    from bclib.options.service_options import ServiceOptions

    config = AppOptions({
        "test": {"value": "test_config"},
        "test1": {"value": "test1_config"}
    })

    opt1 = ServiceOptions("test", config)
    print(f"ServiceOptions('test') content: {dict(opt1)}")

    opt2 = ServiceOptions("test1", config)
    print(f"ServiceOptions('test1') content: {dict(opt2)}")


def test_via_di():
    """Test via DI container"""
    print("\n=== Test 2: Via DI Container ===\n")

    config = {
        "test": {"value": "test_config"},
        "test1": {"value": "test1_config"}
    }

    sp = ServiceProvider()
    add_options_service(sp, config)

    print("Resolving IOptions['test']...")
    opt1 = sp.get_service(IOptions['test'])
    print(f"  Content: {dict(opt1)}")
    print(f"  Type: {type(opt1)}")

    print("\nResolving IOptions['test1']...")
    opt2 = sp.get_service(IOptions['test1'])
    print(f"  Content: {dict(opt2)}")
    print(f"  Type: {type(opt2)}")


if __name__ == "__main__":
    test_direct_creation()
    test_via_di()
