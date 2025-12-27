from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientSession


T = TypeVar('T')


class IRestfulConnection(Generic[T], ABC):
    """
    RESTful HTTP Connection Interface - Async implementation using aiohttp.

    Use this interface for dependency injection without inheritance.
    The generic type parameter T specifies the configuration key.

    Example:
        ```python
        class ApiService:
            def __init__(self, api: IRestfulConnection['external_api']):
                self.api = api

            async def get_users(self):
                return await self.api.get_async('/users')

            async def create_user(self, user_data: dict):
                return await self.api.post_async('/users', json=user_data)
        ```

    Features:
        - Fully async/await using aiohttp
        - No inheritance required
        - Type-safe configuration
        - Easy to mock in tests
        - Similar to ILogger<T> pattern
        - Support for all HTTP methods (GET, POST, PUT, DELETE, PATCH)
        - Configurable timeout, headers, and authentication
    """

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        pass

    @property
    @abstractmethod
    def timeout(self) -> int:
        """Get the request timeout in seconds."""
        pass

    @property
    @abstractmethod
    def headers(self) -> Dict[str, str]:
        """Get the default headers for requests."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if session is active."""
        pass

    @abstractmethod
    async def get_session_async(self) -> 'ClientSession':
        """Get aiohttp ClientSession instance."""
        pass

    @abstractmethod
    async def get_async(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> 'ClientResponse':
        """
        Send GET request to the API.

        Args:
            path: URL path (relative to base_url)
            params: Query parameters
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object

        Example:
            ```python
            response = await api.get_async('/users', params={'page': 1})
            data = await response.json()
            ```
        """
        pass

    @abstractmethod
    async def post_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> 'ClientResponse':
        """
        Send POST request to the API.

        Args:
            path: URL path (relative to base_url)
            json: JSON body data
            data: Form data or other body
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object

        Example:
            ```python
            response = await api.post_async('/users', json={'name': 'John'})
            result = await response.json()
            ```
        """
        pass

    @abstractmethod
    async def put_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> 'ClientResponse':
        """
        Send PUT request to the API.

        Args:
            path: URL path (relative to base_url)
            json: JSON body data
            data: Form data or other body
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object

        Example:
            ```python
            response = await api.put_async('/users/123', json={'name': 'John Updated'})
            result = await response.json()
            ```
        """
        pass

    @abstractmethod
    async def patch_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> 'ClientResponse':
        """
        Send PATCH request to the API.

        Args:
            path: URL path (relative to base_url)
            json: JSON body data
            data: Form data or other body
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object

        Example:
            ```python
            response = await api.patch_async('/users/123', json={'name': 'John'})
            result = await response.json()
            ```
        """
        pass

    @abstractmethod
    async def delete_async(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> 'ClientResponse':
        """
        Send DELETE request to the API.

        Args:
            path: URL path (relative to base_url)
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object

        Example:
            ```python
            response = await api.delete_async('/users/123')
            ```
        """
        pass

    @abstractmethod
    async def close_async(self) -> None:
        """
        Close the HTTP session.

        This method should be called when the connection is no longer needed
        to properly release resources.
        """
        pass
