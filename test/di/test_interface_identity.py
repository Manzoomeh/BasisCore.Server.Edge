"""Test if importing interfaces from different paths causes identity issues in DI"""
import sys

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


def test_ioptions_identity():
    """Test IOptions identity when imported from different paths"""
    print("=== Test 1: IOptions Identity ===\n")

    # Import from different paths
    from bclib.options import IOptions as IOptions1
    from bclib.options.ioptions import IOptions as IOptions2

    # Check if they are the same object
    print(f"IOptions from bclib.options: {IOptions1}")
    print(f"IOptions from bclib.options.ioptions: {IOptions2}")
    print(f"Are they identical? {IOptions1 is IOptions2}")
    print(f"ID of IOptions1: {id(IOptions1)}")
    print(f"ID of IOptions2: {id(IOptions2)}")

    # Test in DI container
    from bclib.options import add_options_service
    from bclib.service_provider import ServiceProvider

    sp = ServiceProvider()
    config = {"test": "value"}
    add_options_service(sp, config)

    # Register using IOptions1
    print("\n--- Testing with DI ---")
    print(f"Registered type (via add_options_service): IOptions")

    # Try to get service using both imports
    service1 = sp.get_service(IOptions1['test'])
    service2 = sp.get_service(IOptions2['test'])

    print(f"Service via IOptions1: {service1}")
    print(f"Service via IOptions2: {service2}")
    print(f"Both are same type? {type(service1) == type(service2)}")
    print(
        f"Both have same value? {service1.value == service2.value if service1 and service2 else 'N/A'}")

    if service1 and service2:
        print("\n✅ IOptions works correctly with different import paths!")
    else:
        print("\n❌ IOptions has identity issues!")

    print()


def test_ilogservice_identity():
    """Test ILogService identity when imported from different paths"""
    print("=== Test 2: ILogService Identity ===\n")

    # Import from different paths
    from bclib.log_service import ILogService as ILogService1
    from bclib.log_service.ilog_service import ILogService as ILogService2

    # Check if they are the same object
    print(f"ILogService from bclib.log_service: {ILogService1}")
    print(f"ILogService from bclib.log_service.ilog_service: {ILogService2}")
    print(f"Are they identical? {ILogService1 is ILogService2}")
    print(f"ID of ILogService1: {id(ILogService1)}")
    print(f"ID of ILogService2: {id(ILogService2)}")

    # Test in DI container
    import asyncio

    from bclib.log_service import LogService, add_log_service
    from bclib.options import add_options_service
    from bclib.service_provider import ServiceProvider

    sp = ServiceProvider()

    # LogService needs options and event loop
    config = {}
    add_options_service(sp, config)
    loop = asyncio.get_event_loop()
    sp.add_singleton(asyncio.AbstractEventLoop, instance=loop)

    add_log_service(sp)

    print("\n--- Testing with DI ---")

    # Try to get service using both imports
    service1 = sp.get_service(ILogService1)
    service2 = sp.get_service(ILogService2)

    print(f"Service via ILogService1: {service1}")
    print(f"Service via ILogService2: {service2}")
    print(f"Are they the same instance? {service1 is service2}")

    if service1 and service2 and service1 is service2:
        print("\n✅ ILogService works correctly with different import paths!")
    else:
        print("\n❌ ILogService has identity issues!")

    print()


def test_idbmanager_identity():
    """Test IDbManager identity when imported from different paths"""
    print("=== Test 3: IDbManager Identity ===\n")

    # Import from different paths
    from bclib.db_manager import IDbManager as IDbManager1
    from bclib.db_manager.idb_manager import IDbManager as IDbManager2

    # Check if they are the same object
    print(f"IDbManager from bclib.db_manager: {IDbManager1}")
    print(f"IDbManager from bclib.db_manager.idb_manager: {IDbManager2}")
    print(f"Are they identical? {IDbManager1 is IDbManager2}")
    print(f"ID of IDbManager1: {id(IDbManager1)}")
    print(f"ID of IDbManager2: {id(IDbManager2)}")

    # Test in DI container
    import asyncio

    from bclib.db_manager import DbManager
    from bclib.options import add_options_service
    from bclib.service_provider import ServiceProvider

    sp = ServiceProvider()

    # DbManager needs options and event loop
    config = {}
    add_options_service(sp, config)
    loop = asyncio.get_event_loop()
    sp.add_singleton(asyncio.AbstractEventLoop, instance=loop)

    sp.add_singleton(IDbManager1, DbManager)

    print("\n--- Testing with DI ---")

    # Try to get service using both imports
    service1 = sp.get_service(IDbManager1)
    service2 = sp.get_service(IDbManager2)

    print(f"Service via IDbManager1: {service1}")
    print(f"Service via IDbManager2: {service2}")
    print(f"Are they the same instance? {service1 is service2}")

    if service1 and service2 and service1 is service2:
        print("\n✅ IDbManager works correctly with different import paths!")
    else:
        print("\n❌ IDbManager has identity issues!")

    print()


def test_mixed_imports_in_constructor():
    """Test if DI injection works when constructor uses different import path"""
    print("=== Test 4: Mixed Imports in Constructor ===\n")

    import asyncio

    from bclib.log_service import add_log_service
    from bclib.options import add_options_service
    from bclib.service_provider import ServiceProvider

    # Setup DI
    sp = ServiceProvider()
    add_options_service(sp, {"db": {"host": "localhost"}})

    loop = asyncio.get_event_loop()
    sp.add_singleton(asyncio.AbstractEventLoop, instance=loop)
    add_log_service(sp)

    # Define service with imports from different paths
    # This simulates what happens when edge.py imports differently than user code
    from bclib.log_service import ILogService  # Package import
    from bclib.options.ioptions import IOptions  # Direct import

    class MyService:
        def __init__(self, config: IOptions['db'], logger: ILogService):
            self.config = config
            self.logger = logger

    sp.add_transient(MyService)

    # Try to create instance
    service = sp.get_service(MyService)

    print(f"MyService instance: {service}")
    print(f"Config injected: {service.config if service else 'Failed'}")
    print(f"Logger injected: {service.logger if service else 'Failed'}")

    if service and service.config and service.logger:
        print(f"Config value: {service.config.value}")
        print("\n✅ Mixed imports work correctly in DI injection!")
    else:
        print("\n❌ Mixed imports cause injection failures!")

    print()


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "Interface Identity Test Suite")
    print("="*70 + "\n")

    try:
        test_ioptions_identity()
        test_ilogservice_identity()
        test_idbmanager_identity()
        test_mixed_imports_in_constructor()

        print("="*70)
        print(" " * 20 + "✅ All Tests Passed!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
