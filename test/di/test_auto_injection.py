"""
Unit tests for automatic DI injection in handlers
"""
import inspect
import unittest
from typing import get_type_hints

from bclib.service_provider import ServiceProvider


class ITestService:
    """Test service interface"""

    def get_value(self) -> str:
        pass


class TestServiceImpl(ITestService):
    """Test service implementation"""

    def __init__(self):
        self.value = "test_value"

    def get_value(self) -> str:
        return self.value


class MockContext:
    """Mock context for testing"""

    def __init__(self, services: ServiceProvider):
        self.services = services


class TestAutomaticDIInjection(unittest.TestCase):
    """Test automatic dependency injection in handlers"""

    def setUp(self):
        """Set up test fixtures"""
        self.services = ServiceProvider()
        self.services.add_singleton(ITestService, TestServiceImpl)
        self.context = MockContext(self.services)

    def test_inject_dependencies_with_service(self):
        """Test _inject_dependencies with a service parameter"""
        # Define a handler with a service parameter
        def handler(context: MockContext, service: ITestService):
            return service.get_value()

        # Simulate _inject_dependencies
        kwargs = self._inject_dependencies(handler, self.context)

        # Verify service was injected
        self.assertIn('service', kwargs)
        self.assertIsInstance(kwargs['service'], TestServiceImpl)
        self.assertEqual(kwargs['service'].get_value(), "test_value")

    def test_inject_dependencies_without_services(self):
        """Test _inject_dependencies with no services"""
        def handler(context: MockContext):
            return "no_service"

        kwargs = self._inject_dependencies(handler, self.context)

        # Verify no kwargs returned
        self.assertEqual(kwargs, {})

    def test_inject_dependencies_with_multiple_services(self):
        """Test _inject_dependencies with multiple service parameters"""
        # Add another service
        class IAnotherService:
            def get_data(self) -> str:
                pass

        class AnotherServiceImpl(IAnotherService):
            def get_data(self) -> str:
                return "another_data"

        self.services.add_transient(IAnotherService, AnotherServiceImpl)

        # Handler with multiple services
        def handler(
            context: MockContext,
            test_service: ITestService,
            another_service: IAnotherService
        ):
            return test_service.get_value() + another_service.get_data()

        kwargs = self._inject_dependencies(handler, self.context)

        # Verify both services injected
        self.assertIn('test_service', kwargs)
        self.assertIn('another_service', kwargs)
        self.assertEqual(kwargs['test_service'].get_value(), "test_value")
        self.assertEqual(kwargs['another_service'].get_data(), "another_data")

    def test_inject_dependencies_skips_context_parameter(self):
        """Test that context parameter is not injected"""
        def handler(context: MockContext, service: ITestService):
            return "ok"

        kwargs = self._inject_dependencies(handler, self.context)

        # Context should not be in kwargs
        self.assertNotIn('context', kwargs)
        # But service should be
        self.assertIn('service', kwargs)

    def test_handler_with_injected_service(self):
        """Test calling a handler with injected service"""
        def handler(context: MockContext, service: ITestService):
            return f"Value: {service.get_value()}"

        # Get injected kwargs
        kwargs = self._inject_dependencies(handler, self.context)

        # Call handler
        result = handler(self.context, **kwargs)

        self.assertEqual(result, "Value: test_value")

    def test_async_handler_with_injected_service(self):
        """Test async handler with injected service"""
        import asyncio

        async def handler(context: MockContext, service: ITestService):
            return f"Async value: {service.get_value()}"

        # Get injected kwargs
        kwargs = self._inject_dependencies(handler, self.context)

        # Call async handler
        result = asyncio.run(handler(self.context, **kwargs))

        self.assertEqual(result, "Async value: test_value")

    def test_inject_dependencies_with_unregistered_service(self):
        """Test that unregistered services are not injected"""
        class IUnregisteredService:
            pass

        def handler(context: MockContext, service: IUnregisteredService):
            return "ok"

        kwargs = self._inject_dependencies(handler, self.context)

        # Unregistered service should not be in kwargs
        self.assertNotIn('service', kwargs)

    # Helper method to simulate _inject_dependencies from Dispatcher
    def _inject_dependencies(self, handler, context):
        """
        Simulate the _inject_dependencies method from Dispatcher class
        """
        kwargs = {}

        try:
            # Check if DI is available
            if not hasattr(context, 'services'):
                return kwargs

            # Get handler signature
            sig = inspect.signature(handler)
            type_hints = get_type_hints(handler)

            # Iterate through parameters
            for param_name, param in sig.parameters.items():
                # Get type hint
                param_type = type_hints.get(param_name)

                if param_type is None:
                    continue

                # Check if it's a Context type (already provided)
                if isinstance(context, param_type):
                    continue

                # Try to resolve from DI container
                if hasattr(context, 'services') and context.services:
                    service = context.services.get_service(param_type)
                    if service is not None:
                        kwargs[param_name] = service

        except Exception:
            # If DI fails, continue without injection
            pass

        return kwargs


if __name__ == "__main__":
    unittest.main()
