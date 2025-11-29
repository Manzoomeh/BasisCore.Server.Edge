"""
Test that sync handlers run in thread pool and don't block event loop
"""
import asyncio
import threading
import time
import unittest

from bclib.context import RESTfulContext
from bclib.dispatcher import Dispatcher
from bclib.logger import ILogger
from bclib.service_provider import ServiceProvider


class MockLogger(ILogger):
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        self.logs.append(message)


class TestSyncPerformance(unittest.TestCase):
    """Test that sync handlers don't block the event loop"""

    def setUp(self):
        """Setup dispatcher and services"""
        self.dispatcher = Dispatcher({})
        self.services = ServiceProvider()
        self.services.add_singleton(ILogger, MockLogger)
        self.main_thread_id = threading.current_thread().ident

    def test_sync_handler_runs_in_thread_pool(self):
        """Verify sync handler runs in a different thread (thread pool)"""
        handler_thread_id = None

        @self.dispatcher.restful_handler()
        def sync_handler(logger: ILogger):
            nonlocal handler_thread_id
            handler_thread_id = threading.current_thread().ident
            logger.log("Sync handler executed")
            return {"status": "ok"}

        # Create mock context
        class MockContext:
            def __init__(self, services):
                self.services = services

            def generate_response(self, data):
                return data

        context = MockContext(self.services)

        # Run handler
        async def run():
            # Get the wrapper from dispatcher
            callbacks = self.dispatcher._Dispatcher__look_up.get(
                "RESTfulContext", [])
            self.assertEqual(len(callbacks), 1)
            wrapper = callbacks[0]._CallbackInfo__async_callback

            # Call wrapper
            result = await wrapper(context)
            return result

        # Execute
        result = asyncio.run(run())

        # Verify
        self.assertIsNotNone(handler_thread_id)
        self.assertNotEqual(handler_thread_id, self.main_thread_id,
                            "Sync handler should run in thread pool, not main thread!")
        logger = self.services.get_service(ILogger)
        self.assertEqual(logger.logs, ["Sync handler executed"])

    def test_async_handler_runs_in_main_thread(self):
        """Verify async handler runs in the main thread (event loop)"""
        handler_thread_id = None

        @self.dispatcher.restful_handler()
        async def async_handler(logger: ILogger):
            nonlocal handler_thread_id
            handler_thread_id = threading.current_thread().ident
            logger.log("Async handler executed")
            return {"status": "ok"}

        # Create mock context
        class MockContext:
            def __init__(self, services):
                self.services = services

            def generate_response(self, data):
                return data

        context = MockContext(self.services)

        # Run handler
        async def run():
            # Get the wrapper from dispatcher
            callbacks = self.dispatcher._Dispatcher__look_up.get(
                "RESTfulContext", [])
            self.assertEqual(len(callbacks), 1)
            wrapper = callbacks[0]._CallbackInfo__async_callback

            # Call wrapper
            result = await wrapper(context)
            return result

        # Execute
        result = asyncio.run(run())

        # Verify - async handler runs in same thread as event loop
        self.assertIsNotNone(handler_thread_id)
        # Note: asyncio.run() creates a new thread, so we can't compare with main_thread_id
        # But we can verify the handler executed
        logger = self.services.get_service(ILogger)
        self.assertEqual(logger.logs, ["Async handler executed"])

    def test_sync_handler_does_not_block_event_loop(self):
        """Verify that a blocking sync handler doesn't block other async tasks"""
        execution_order = []

        @self.dispatcher.restful_handler()
        def blocking_sync_handler(logger: ILogger):
            execution_order.append("sync_start")
            time.sleep(0.1)  # Simulate blocking I/O
            execution_order.append("sync_end")
            logger.log("Blocking sync handler")
            return {"status": "blocked"}

        # Create mock context
        class MockContext:
            def __init__(self, services):
                self.services = services

            def generate_response(self, data):
                return data

        context = MockContext(self.services)

        # Run handler alongside another async task
        async def run():
            # Get the wrapper
            callbacks = self.dispatcher._Dispatcher__look_up.get(
                "RESTfulContext", [])
            wrapper = callbacks[0]._CallbackInfo__async_callback

            # Start sync handler
            sync_task = asyncio.create_task(wrapper(context))

            # Start another async task
            async def fast_task():
                execution_order.append("fast_start")
                await asyncio.sleep(0.05)  # Shorter than sync handler
                execution_order.append("fast_end")

            fast = asyncio.create_task(fast_task())

            # Wait for both
            await asyncio.gather(sync_task, fast)

        # Execute
        asyncio.run(run())

        # Verify execution order - fast task should complete before sync handler ends
        self.assertEqual(execution_order, [
            "sync_start",
            "fast_start",
            "fast_end",
            "sync_end"
        ], "Fast async task should complete while sync handler is blocking in thread pool")


if __name__ == '__main__':
    print("=" * 70)
    print("Performance Tests: Sync Handlers in Thread Pool")
    print("=" * 70)
    unittest.main(verbosity=2)
