"""
Hosted Service Interface - Contract for services with startup and shutdown lifecycle

Defines the contract for services that need to perform initialization
and cleanup operations during application startup and shutdown.
"""
from abc import ABC


class IHostedService(ABC):
    """
    Interface for services with startup and shutdown lifecycle

    Services implementing this interface can perform async initialization
    when the application starts and graceful cleanup when it stops.

    Lifecycle:
        - start_async(): Called during application startup (in dispatcher.initialize_task)
        - stop_async(): Called during application shutdown (before event loop stops)

    Example:
        ```python
        class BackgroundWorker(IHostedService):
            async def start_async(self):
                print("Starting background worker...")
                # Initialize connections, start tasks, etc.

            async def stop_async(self):
                print("Stopping background worker...")
                # Close connections, cancel tasks, cleanup, etc.

        # Register as hosted service
        dispatcher.services.add_singleton(IHostedService, BackgroundWorker, is_hosted=True)
        ```
    """

    async def start_async(self) -> None:
        """
        Initialize service when application starts

        Called during application startup (in dispatcher.initialize_task).
        Use this to initialize connections, start background tasks, etc.

        Example:
            ```python
            async def start_async(self):
                self.connection = await connect_to_database()
                self.task = asyncio.create_task(self.background_loop())
                print("Service started successfully")
            ```
        """
        pass

    async def stop_async(self) -> None:
        """
        Cleanup service when application stops

        Called during graceful shutdown (before event loop stops).
        Use this to close connections, cancel tasks, flush buffers, etc.

        Example:
            ```python
            async def stop_async(self):
                if self.task:
                    self.task.cancel()
                if self.connection:
                    await self.connection.close()
                print("Service stopped gracefully")
            ```
        """
        pass
