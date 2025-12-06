"""Test ForwardRef and string annotations support in DI"""
from __future__ import \
    annotations  # Enable string annotations - must be first!

import sys
from typing import ForwardRef

from bclib.options import IOptions, add_options_service
from bclib.service_provider import InjectionPlan, ServiceProvider

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


def test_string_annotations():
    """Test string annotations (from __future__ import annotations)"""
    print("=== Test 1: String Annotations Support ===\n")

    config = {
        "database": {"host": "localhost", "port": 5432},
        "cache": {"host": "redis.local", "port": 6379}
    }

    sp = ServiceProvider()
    add_options_service(sp, config)

    # With __future__ annotations, all type hints become strings
    class MyService:
        def __init__(self, db_options: IOptions['database'], cache_options: IOptions['cache']):
            self.db_options = db_options
            self.cache_options = cache_options

    # Check InjectionPlan
    plan = InjectionPlan(MyService)
    print(f"Parameters detected: {list(plan.param_strategies.keys())}")

    for name, strategy in plan.param_strategies.items():
        print(f"  {name}: {type(strategy).__name__}")
        if hasattr(strategy, 'target_type'):
            print(f"    Type: {strategy.target_type}")

    print()

    # Create instance
    sp.add_transient(MyService)
    service = sp.get_service(MyService)

    print(f"Database config: {service.db_options.value}")
    print(f"Cache config: {service.cache_options.value}")

    print("\n✅ String annotations test passed!\n")


def test_forward_ref_explicit():
    """Test explicit ForwardRef handling"""
    print("=== Test 2: Explicit ForwardRef Handling ===\n")

    config = {
        "api": {"key": "secret123", "version": "v1"},
    }

    sp = ServiceProvider()
    add_options_service(sp, config)

    # Test direct service resolution
    print("Resolving IOptions['api']...")
    api_options = sp.get_service(IOptions['api'])

    print(f"API config: {api_options.value}")
    print(f"API key: {api_options.get('key')}")

    print("\n✅ ForwardRef test passed!\n")


def test_mixed_annotations():
    """Test mixed type hints (some with annotations, some without)"""
    print("=== Test 3: Mixed Type Hints ===\n")

    config = {
        "server": {"host": "0.0.0.0", "port": 8080},
        "timeout": 30
    }

    sp = ServiceProvider()
    add_options_service(sp, config)

    # Mixed annotations: regular type + IOptions
    class WebServer:
        def __init__(
            self,
            name: str,  # This should be injected from kwargs
            config: IOptions['server']
        ):
            self.name = name
            self.config = config

    plan = InjectionPlan(WebServer)
    print(f"Detected parameters: {list(plan.param_strategies.keys())}")

    for param_name, strategy in plan.param_strategies.items():
        print(f"  {param_name}: {type(strategy).__name__}")

    print()

    sp.add_transient(WebServer)

    # Provide name via kwargs
    server = sp.create_instance(WebServer, name="MyServer")

    print(f"Server name: {server.name}")
    print(f"Server config: {server.config.value}")
    print(f"Server host: {server.config.get('host')}")

    print("\n✅ Mixed annotations test passed!\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "ForwardRef & Annotations Test Suite")
    print("="*70 + "\n")

    try:
        test_string_annotations()
        test_forward_ref_explicit()
        test_mixed_annotations()

        print("="*70)
        print(" " * 10 + "✅ All ForwardRef & Annotations Tests Passed!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
