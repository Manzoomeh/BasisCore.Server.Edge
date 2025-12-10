"""Test HttpListener factory with multiple configurations"""

from bclib.listener.http.http_listener import HttpListener
from bclib.listener.listener_factory import ListenerFactory
from bclib.options.app_options import AppOptions
from bclib.service_provider import ServiceProvider


def test_single_string_endpoint():
    """Test with simple string endpoint"""
    print("=== Test 1: Simple String Endpoint ===\n")

    options = AppOptions({
        "http": "localhost:8080"
    })

    sp = ServiceProvider()
    factory = ListenerFactory(sp, options)
    listeners = factory.load_listeners()

    print(f"Created {len(listeners)} listener(s)")
    assert len(listeners) == 1, f"Expected 1 listener, got {len(listeners)}"
    assert isinstance(listeners[0], HttpListener), "Should be HttpListener"

    print("✅ Single string endpoint works!\n")
    return True


def test_array_of_strings():
    """Test with array of string endpoints"""
    print("=== Test 2: Array of String Endpoints ===\n")

    options = AppOptions({
        "http": [
            "localhost:8080",
            "localhost:8081",
            "0.0.0.0:9000"
        ]
    })

    sp = ServiceProvider()
    factory = ListenerFactory(sp, options)
    listeners = factory.load_listeners()

    print(f"Created {len(listeners)} listener(s)")
    assert len(listeners) == 3, f"Expected 3 listeners, got {len(listeners)}"

    for i, listener in enumerate(listeners):
        assert isinstance(
            listener, HttpListener), f"Listener {i} should be HttpListener"

    print("✅ Array of strings works!\n")
    return True


def test_array_with_mixed_configs():
    """Test with array containing strings and dicts"""
    print("=== Test 3: Mixed Array (Strings + Dicts) ===\n")

    options = AppOptions({
        "http": [
            "localhost:8080",  # Simple string
            {
                "endpoint": "localhost:8443",
                "ssl": {
                    "certfile": "cert.pem",
                    "keyfile": "key.pem"
                }
            },
            {
                "endpoint": "0.0.0.0:9000",
                "config": {
                    "router": "restful"
                }
            }
        ]
    })

    sp = ServiceProvider()
    factory = ListenerFactory(sp, options)
    listeners = factory.load_listeners()

    print(f"Created {len(listeners)} listener(s)")
    assert len(listeners) == 3, f"Expected 3 listeners, got {len(listeners)}"

    print("✅ Mixed array works!\n")
    return True


def test_global_ssl_merge():
    """Test that global SSL merges into items without SSL"""
    print("=== Test 4: Global SSL Merge ===\n")

    options = AppOptions({
        "http": [
            "localhost:8080",
            "localhost:8081"
        ],
        "ssl": {
            "certfile": "global.pem",
            "keyfile": "global-key.pem"
        }
    })

    sp = ServiceProvider()
    factory = ListenerFactory(sp, options)
    listeners = factory.load_listeners()

    print(f"Created {len(listeners)} listener(s) with global SSL")
    assert len(listeners) == 2, f"Expected 2 listeners, got {len(listeners)}"

    print("✅ Global SSL merge works!\n")
    return True


def test_single_dict_config():
    """Test with single dict configuration"""
    print("=== Test 5: Single Dict Config ===\n")

    options = AppOptions({
        "http": {
            "endpoint": "localhost:8080",
            "ssl": {"certfile": "cert.pem", "keyfile": "key.pem"},
            "config": {"router": "restful"}
        }
    })

    sp = ServiceProvider()
    factory = ListenerFactory(sp, options)
    listeners = factory.load_listeners()

    print(f"Created {len(listeners)} listener(s)")
    assert len(listeners) == 1, f"Expected 1 listener, got {len(listeners)}"

    print("✅ Single dict config works!\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "HttpListener Factory Tests")
    print("="*70 + "\n")

    try:
        results = []
        results.append(test_single_string_endpoint())
        results.append(test_array_of_strings())
        results.append(test_array_with_mixed_configs())
        results.append(test_global_ssl_merge())
        results.append(test_single_dict_config())

        print("="*70)
        if all(results):
            print("✅ ALL TESTS PASSED!")
            print("\nSupported http configurations:")
            print("  1. String: \"localhost:8080\"")
            print(
                "  2. Array of strings: [\"localhost:8080\", \"localhost:8081\"]")
            print(
                "  3. Dict: {\"endpoint\": \"...\", \"ssl\": {...}, \"config\": {...}}")
            print("  4. Array of dicts/strings (mixed)")
            print("  5. Global SSL merged into items without SSL")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
