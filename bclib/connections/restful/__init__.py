"""RESTful HTTP Connection Module

Provides modern RESTful HTTP client connection management inspired by ILogger<T> pattern.
No inheritance required - use IRestfulConnection[TConfig] directly in your services.

Features:
    - Async HTTP methods (GET, POST, PUT, PATCH, DELETE)
    - Configurable base URL, timeout, and headers
    - Connection pooling with aiohttp
    - Type-safe configuration through generics
    - No inheritance required
    - Easy integration with services

Example:
    ```python
    from bclib.connections.restful import IRestfulConnection, add_restful_connection
    
    # Register RESTful connections
    add_restful_connection(services)
    
    # Use in service
    class UserService:
        def __init__(self, api: IRestfulConnection['external_api']):
            self.api = api
        
        async def get_users(self):
            response = await self.api.get_async('/users')
            return await response.json()
        
        async def create_user(self, name: str, email: str):
            user_data = {'name': name, 'email': email}
            response = await self.api.post_async('/users', json=user_data)
            return await response.json()
        
        async def update_user(self, user_id: str, data: dict):
            response = await self.api.put_async(f'/users/{user_id}', json=data)
            return await response.json()
        
        async def delete_user(self, user_id: str):
            response = await self.api.delete_async(f'/users/{user_id}')
            return response.status == 200
    ```

Configuration (in host.json):
    ```json
    {
        "external_api": {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "headers": {
                "Authorization": "Bearer your_token_here",
                "Content-Type": "application/json",
                "User-Agent": "YourApp/1.0"
            }
        },
        "payment_api": {
            "base_url": "https://payment.example.com/api/v1",
            "timeout": 60,
            "headers": {
                "X-API-Key": "your_api_key"
            }
        }
    }
    ```
"""

from bclib.di import IServiceContainer

from .irestful_connection import IRestfulConnection

__all__ = ['IRestfulConnection', 'add_restful_connection']


def add_restful_connection(service_container: IServiceContainer) -> IServiceContainer:
    """
    Register RESTful Connection Services in DI Container

    Adds RestfulConnection as the implementation for IRestfulConnection[T] in the service provider.
    This allows you to inject IRestfulConnection[TConfig] directly into your services without
    inheritance - similar to ILogger<T> pattern.

    Args:
        service_container: The DI container to register services in

    Returns:
        The service container (for chaining)

    Example:
        ```python
        from bclib import edge
        from bclib.connections.restful import add_restful_connection

        # Create dispatcher
        app = edge.from_options({
            "http": "localhost:8080",
            "external_api": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "headers": {
                    "Authorization": "Bearer token"
                }
            }
        })

        # Register RESTful connections
        add_restful_connection(app.services)

        # Use in handler
        @app.restful_handler("api/proxy/:endpoint")
        async def proxy_handler(
            context: RESTfulContext,
            api: IRestfulConnection['external_api']
        ):
            endpoint = context.url_segments['endpoint']
            response = await api.get_async(f'/{endpoint}')
            data = await response.json()
            return data
        ```

    Configuration Structure:
        Each connection configuration should have:
        - base_url (required): Base URL for all API requests
        - timeout (optional): Request timeout in seconds (default: 30)
        - headers (optional): Default headers for all requests

        Example:
        ```json
        {
            "my_api": {
                "base_url": "https://api.example.com/v1",
                "timeout": 60,
                "headers": {
                    "Authorization": "Bearer token",
                    "Content-Type": "application/json"
                }
            }
        }
        ```
    """

    from bclib.di import IServiceProvider, extract_generic_type_key
    from bclib.options import IOptions

    from .restful_connection import RestfulConnection

    def create_restful_connection(service_provider: IServiceProvider, **kwargs):
        """
        Factory function for creating RestfulConnection instances.

        This factory is called by the DI container when resolving IRestfulConnection[T].
        It extracts the configuration key from generic type arguments and creates
        a RestfulConnection with the appropriate configuration.

        Args:
            service_provider: Service provider for resolving dependencies
            **kwargs: Contains 'generic_type_args' with configuration key

        Returns:
            RestfulConnection instance configured for the specified key

        Note:
            This is an internal factory function. Use add_restful_connection() to register
            the service, then inject IRestfulConnection[TConfig] in your services.
        """
        # Extract configuration key from generic type arguments
        key = extract_generic_type_key(kwargs)

        # Get configuration options for this key
        options = service_provider.get_service(IOptions[key])

        # Create and return RestfulConnection
        return service_provider.create_instance(RestfulConnection, options=options, **kwargs)

    return service_container.add_transient(
        IRestfulConnection,
        factory=create_restful_connection
    )
