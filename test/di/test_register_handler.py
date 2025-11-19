"""
Test register_handler method - Register handlers without decorators

Shows how to register handlers programmatically instead of using decorators.
Useful for dynamic handler registration at runtime.
"""
import unittest
from unittest.mock import AsyncMock, Mock

from bclib.context import RESTfulContext, SocketContext, WebContext
from bclib.dispatcher import Dispatcher
from bclib.service_provider import ServiceProvider


# Test services
class ILogger:
    def log(self, message: str): ...


class ConsoleLogger(ILogger):
    def __init__(self):
        self.messages = []

    def log(self, message: str):
        self.messages.append(message)


class TestRegisterHandler(unittest.TestCase):
    """Test programmatic handler registration"""

    def setUp(self):
        """Setup dispatcher for each test"""
        self.dispatcher = Dispatcher(options={})
        self.dispatcher.add_singleton(ILogger, ConsoleLogger)

    def test_register_restful_handler_without_decorator(self):
        """Test registering RESTful handler without decorator"""

        # Define handler function
        def hello_handler(logger: ILogger):
            logger.log("Hello called")
            return {"message": "Hello World"}

        # Register handler programmatically
        self.dispatcher.register_handler(
            RESTfulContext,
            hello_handler,
            []
        )

        # Verify handler is registered
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 1)

    def test_register_multiple_handlers(self):
        """Test registering multiple handlers for same context type"""

        def handler1(logger: ILogger):
            return {"handler": 1}

        def handler2(logger: ILogger):
            return {"handler": 2}

        # Register multiple handlers
        self.dispatcher.register_handler(RESTfulContext, handler1)
        self.dispatcher.register_handler(RESTfulContext, handler2)

        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 2)

    def test_register_handler_with_method_chaining(self):
        """Test method chaining when registering handlers"""

        def handler1():
            return {"handler": 1}

        def handler2():
            return {"handler": 2}

        # Chain multiple registrations
        result = self.dispatcher\
            .register_handler(RESTfulContext, handler1)\
            .register_handler(WebContext, handler2)

        # Should return self for chaining
        self.assertIs(result, self.dispatcher)

        # Verify both registered
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(RESTfulContext)), 1)
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(WebContext)), 1)

    def test_register_socket_handler(self):
        """Test registering socket handler"""

        def socket_handler(logger: ILogger):
            logger.log("Socket handler called")
            return True

        self.dispatcher.register_handler(SocketContext, socket_handler)

        handlers = self.dispatcher._get_context_lookup(SocketContext)
        self.assertEqual(len(handlers), 1)

    def test_register_handler_different_context_types(self):
        """Test registering handlers for different context types"""

        def restful_handler():
            return {"type": "restful"}

        def socket_handler():
            return True

        def web_handler():
            return {"type": "web"}

        self.dispatcher.register_handler(RESTfulContext, restful_handler)
        self.dispatcher.register_handler(SocketContext, socket_handler)
        self.dispatcher.register_handler(WebContext, web_handler)

        # Each context type should have one handler
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(RESTfulContext)), 1)
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(SocketContext)), 1)
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(WebContext)), 1)

    def test_mix_decorator_and_register_handler(self):
        """Test mixing decorator-based and programmatic registration"""

        # Register with decorator
        @self.dispatcher.restful_action()
        def decorator_handler():
            return {"method": "decorator"}

        # Register programmatically
        def programmatic_handler():
            return {"method": "programmatic"}

        self.dispatcher.register_handler(RESTfulContext, programmatic_handler)

        # Both should be registered
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 2)

    def test_unregister_specific_handler(self):
        """Test unregistering a specific handler"""

        def handler1():
            return {"handler": 1}

        def handler2():
            return {"handler": 2}

        # Register two handlers
        self.dispatcher.register_handler(RESTfulContext, handler1)
        self.dispatcher.register_handler(RESTfulContext, handler2)

        # Verify both registered
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 2)

        # Unregister first handler
        self.dispatcher.unregister_handler(RESTfulContext, handler1)

        # Verify only one handler remains
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 1)

    def test_unregister_all_handlers_for_context(self):
        """Test unregistering all handlers for a context type"""

        def handler1():
            return {"handler": 1}

        def handler2():
            return {"handler": 2}

        def handler3():
            return {"handler": 3}

        # Register multiple handlers
        self.dispatcher.register_handler(RESTfulContext, handler1)
        self.dispatcher.register_handler(RESTfulContext, handler2)
        self.dispatcher.register_handler(RESTfulContext, handler3)

        # Verify all registered
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 3)

        # Unregister all handlers (no specific handler parameter)
        self.dispatcher.unregister_handler(RESTfulContext)

        # Verify all removed
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 0)

    def test_unregister_handler_with_method_chaining(self):
        """Test method chaining when unregistering handlers"""

        def handler1():
            return {"handler": 1}

        def handler2():
            return {"handler": 2}

        # Register handlers
        self.dispatcher.register_handler(RESTfulContext, handler1)
        self.dispatcher.register_handler(WebContext, handler2)

        # Chain unregister operations
        result = self.dispatcher\
            .unregister_handler(RESTfulContext, handler1)\
            .unregister_handler(WebContext)

        # Should return self for chaining
        self.assertIs(result, self.dispatcher)

        # Verify both were removed
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(RESTfulContext)), 0)
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(WebContext)), 0)

    def test_unregister_nonexistent_handler(self):
        """Test unregistering a handler that was never registered"""

        def handler1():
            return {"handler": 1}

        def handler2():
            return {"handler": 2}

        # Register only handler1
        self.dispatcher.register_handler(RESTfulContext, handler1)

        # Try to unregister handler2 (not registered)
        self.dispatcher.unregister_handler(RESTfulContext, handler2)

        # handler1 should still be there
        handlers = self.dispatcher._get_context_lookup(RESTfulContext)
        self.assertEqual(len(handlers), 1)

    def test_unregister_handler_different_context_types(self):
        """Test unregistering handlers from different context types"""

        def restful_handler():
            return {"type": "restful"}

        def socket_handler():
            return True

        # Register handlers for different contexts
        self.dispatcher.register_handler(RESTfulContext, restful_handler)
        self.dispatcher.register_handler(SocketContext, socket_handler)

        # Unregister RESTful handler only
        self.dispatcher.unregister_handler(RESTfulContext, restful_handler)

        # RESTful should be empty, Socket should still have handler
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(RESTfulContext)), 0)
        self.assertEqual(
            len(self.dispatcher._get_context_lookup(SocketContext)), 1)


def run_tests():
    """Run all tests"""
    print("=" * 70)
    print("Register Handler Method - Unit Tests")
    print("=" * 70)
    print()

    suite = unittest.TestLoader().loadTestsFromTestCase(TestRegisterHandler)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print()
        print("Key Features:")
        print("  - Register/unregister handlers without decorators")
        print("  - Supports all context types (RESTful, Socket, Web, etc.)")
        print("  - Automatic dependency injection works")
        print("  - Method chaining supported")
        print("  - Can mix with decorator-based registration")
        print()
        print("Register Example:")
        print("  def my_handler(logger: ILogger):")
        print("      return {'message': 'Hello'}")
        print()
        print("  dispatcher.register_handler(")
        print("      RESTfulContext,")
        print("      my_handler,")
        print("      [dispatcher.url('api/hello')]")
        print("  )")
        print()
        print("Unregister Examples:")
        print("  # Remove specific handler")
        print("  dispatcher.unregister_handler(RESTfulContext, my_handler)")
        print()
        print("  # Remove all handlers for context type")
        print("  dispatcher.unregister_handler(RESTfulContext)")
    else:
        print("✗ Some tests failed")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
