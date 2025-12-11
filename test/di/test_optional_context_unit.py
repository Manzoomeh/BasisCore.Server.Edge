"""Unit test for optional context parameter in handlers"""
import inspect
import unittest
from typing import get_type_hints

from bclib.di import ServiceProvider


class ILogger:
    def log(self, msg: str):
        pass


class ConsoleLogger(ILogger):
    def log(self, msg: str):
        print(f"[LOG] {msg}")


class MockContext:
    def __init__(self, services: ServiceProvider):
        self.__services = services

    @property
    def services(self):
        return self.__services


class TestOptionalContextInjection(unittest.TestCase):
    """Test that context can be optional in handlers"""

    def setUp(self):
        """Setup DI container"""
        self.services = ServiceProvider()
        self.services.add_singleton(ILogger, ConsoleLogger)
        self.context = MockContext(self.services)

    def test_handler_with_context_only(self):
        """Handler that only needs context"""
        def handler(context: MockContext):
            return f"has_context: {context is not None}"

        # Inject dependencies
        injected = self.services.inject_dependencies(handler, self.context)

        # Context should not be injected (already in args)
        self.assertEqual(len(injected), 0)

        # Call handler
        result = handler(self.context, **injected)
        self.assertEqual(result, "has_context: True")

    def test_handler_with_logger_only(self):
        """Handler that only needs logger (no context parameter!)"""
        def handler(logger: ILogger):
            logger.log("Called without context")
            return "logger_injected"

        # Inject dependencies - should inject logger
        injected = self.services.inject_dependencies(handler, self.context)

        # Logger should be injected
        self.assertIn('logger', injected)
        self.assertIsInstance(injected['logger'], ILogger)

        # Call handler WITHOUT context parameter
        result = handler(**injected)
        self.assertEqual(result, "logger_injected")

    def test_handler_with_both(self):
        """Handler with both context and logger"""
        def handler(context: MockContext, logger: ILogger):
            logger.log("Has both")
            return f"context: {context is not None}"

        # Inject dependencies
        injected = self.services.inject_dependencies(handler, self.context)

        # Only logger should be injected (context in args)
        self.assertIn('logger', injected)
        self.assertNotIn('context', injected)  # Already in args

        # Call handler
        result = handler(self.context, **injected)
        self.assertEqual(result, "context: True")

    def test_handler_signature_detection(self):
        """Test that we can detect if handler needs context"""
        def with_context(context: MockContext):
            pass

        def without_context(logger: ILogger):
            pass

        def with_both(context: MockContext, logger: ILogger):
            pass

        # Check signatures
        sig1 = inspect.signature(with_context)
        hints1 = get_type_hints(with_context)
        self.assertIn('context', hints1)

        sig2 = inspect.signature(without_context)
        hints2 = get_type_hints(without_context)
        self.assertNotIn('context', hints2)
        self.assertIn('logger', hints2)

        sig3 = inspect.signature(with_both)
        hints3 = get_type_hints(with_both)
        self.assertIn('context', hints3)
        self.assertIn('logger', hints3)

    def test_inject_dependencies_skips_context_in_args(self):
        """Verify inject_dependencies skips context when it's in args"""
        def handler(context: MockContext, logger: ILogger):
            pass

        # When context is in args, it should not be injected
        injected = self.services.inject_dependencies(handler, self.context)

        # Context should NOT be in injected (already in args)
        self.assertNotIn('context', injected)

        # Logger should be injected
        self.assertIn('logger', injected)


if __name__ == '__main__':
    print("=" * 70)
    print("Unit Tests: Optional Context Parameter in Handlers")
    print("=" * 70)
    unittest.main(verbosity=2)
