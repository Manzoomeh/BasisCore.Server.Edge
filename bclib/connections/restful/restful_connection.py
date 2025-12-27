"""RESTful HTTP Connection - Async implementation using aiohttp"""
import asyncio
from typing import Any, Dict, Generic, Optional, TypeVar

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout

from bclib.logger.ilogger import ILogger
from bclib.options import IOptions

from .irestful_connection import IRestfulConnection

T = TypeVar('T')


class RestfulConnection(IRestfulConnection[T], Generic[T]):
    """
    RESTful HTTP Connection - Async HTTP client using aiohttp.

    Features:
        - Async HTTP methods (GET, POST, PUT, PATCH, DELETE)
        - Configurable base URL, timeout, and headers
        - Session management with connection pooling
        - Type-safe configuration through generics
        - Automatic session cleanup

    Configuration (in host.json):
        ```json
        {
            "external_api": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "headers": {
                    "Authorization": "Bearer token",
                    "Content-Type": "application/json"
                }
            }
        }
        ```

    Usage:
        ```python
        class UserService:
            def __init__(self, api: IRestfulConnection['external_api']):
                self.api = api

            async def get_users(self):
                response = await self.api.get_async('/users')
                return await response.json()

            async def create_user(self, name: str):
                response = await self.api.post_async('/users', json={'name': name})
                return await response.json()
        ```
    """

    def __init__(
        self,
        options: IOptions['RestfulConnection[T]'],
        logger: ILogger['RestfulConnection[T]']
    ):
        """
        Initialize RESTful connection.

        Args:
            options: Configuration options for this connection
            logger: Optional logger for connection events
        """
        self._options = options
        self._logger = logger
        self._session: Optional[ClientSession] = None
        self._session_lock = asyncio.Lock()

        # Parse configuration
        self._base_url = self._options.get('base_url', '')
        self._timeout = self._options.get('timeout', 30)
        self._default_headers = self._options.get('headers', {})

        if not self._base_url:
            raise ValueError(
                f"Configuration key '{options.key}' must contain 'base_url'")

        if self._logger:
            self._logger.info(
                f"RestfulConnection initialized for {self._base_url}")

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return self._base_url

    @property
    def timeout(self) -> int:
        """Get the request timeout in seconds."""
        return self._timeout

    @property
    def headers(self) -> Dict[str, str]:
        """Get the default headers for requests."""
        return self._default_headers.copy()

    @property
    def is_connected(self) -> bool:
        """Check if session is active."""
        return self._session is not None and not self._session.closed

    async def get_session_async(self) -> ClientSession:
        """
        Get or create aiohttp ClientSession.

        Uses lazy initialization and ensures thread-safe session creation.

        Returns:
            ClientSession instance
        """
        if self._session is None or self._session.closed:
            async with self._session_lock:
                # Double-check after acquiring lock
                if self._session is None or self._session.closed:
                    timeout = ClientTimeout(total=self._timeout)
                    self._session = ClientSession(
                        headers=self._default_headers,
                        timeout=timeout
                    )
                    if self._logger:
                        self._logger.debug(
                            f"Created new HTTP session for {self._base_url}")

        return self._session

    def _build_url(self, path: str) -> str:
        """Build full URL from base URL and path."""
        # Remove leading slash from path if present
        path = path.lstrip('/')
        # Ensure base_url doesn't end with slash
        base = self._base_url.rstrip('/')
        return f"{base}/{path}"

    def _merge_headers(self, additional_headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge default headers with additional headers."""
        if additional_headers:
            merged = self._default_headers.copy()
            merged.update(additional_headers)
            return merged
        return self._default_headers

    async def get_async(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ClientResponse:
        """
        Send GET request to the API.

        Args:
            path: URL path (relative to base_url)
            params: Query parameters
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object
        """
        session = await self.get_session_async()
        url = self._build_url(path)
        merged_headers = self._merge_headers(headers)

        if self._logger:
            self._logger.debug(f"GET {url}")

        timeout_obj = ClientTimeout(
            total=timeout) if timeout else ClientTimeout(total=self._timeout)

        return await session.get(
            url,
            params=params,
            headers=merged_headers,
            timeout=timeout_obj
        )

    async def post_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ClientResponse:
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
        """
        session = await self.get_session_async()
        url = self._build_url(path)
        merged_headers = self._merge_headers(headers)

        if self._logger:
            self._logger.debug(f"POST {url}")

        timeout_obj = ClientTimeout(
            total=timeout) if timeout else ClientTimeout(total=self._timeout)

        return await session.post(
            url,
            json=json,
            data=data,
            headers=merged_headers,
            timeout=timeout_obj
        )

    async def put_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ClientResponse:
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
        """
        session = await self.get_session_async()
        url = self._build_url(path)
        merged_headers = self._merge_headers(headers)

        if self._logger:
            self._logger.debug(f"PUT {url}")

        timeout_obj = ClientTimeout(
            total=timeout) if timeout else ClientTimeout(total=self._timeout)

        return await session.put(
            url,
            json=json,
            data=data,
            headers=merged_headers,
            timeout=timeout_obj
        )

    async def patch_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ClientResponse:
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
        """
        session = await self.get_session_async()
        url = self._build_url(path)
        merged_headers = self._merge_headers(headers)

        if self._logger:
            self._logger.debug(f"PATCH {url}")

        timeout_obj = ClientTimeout(
            total=timeout) if timeout else ClientTimeout(total=self._timeout)

        return await session.patch(
            url,
            json=json,
            data=data,
            headers=merged_headers,
            timeout=timeout_obj
        )

    async def delete_async(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ClientResponse:
        """
        Send DELETE request to the API.

        Args:
            path: URL path (relative to base_url)
            headers: Additional headers (merged with default headers)
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ClientResponse object
        """
        session = await self.get_session_async()
        url = self._build_url(path)
        merged_headers = self._merge_headers(headers)

        if self._logger:
            self._logger.debug(f"DELETE {url}")

        timeout_obj = ClientTimeout(
            total=timeout) if timeout else ClientTimeout(total=self._timeout)

        return await session.delete(
            url,
            headers=merged_headers,
            timeout=timeout_obj
        )

    async def close_async(self) -> None:
        """
        Close the HTTP session.

        This method should be called when the connection is no longer needed
        to properly release resources.
        """
        if self._session and not self._session.closed:
            if self._logger:
                self._logger.info(f"Closing HTTP session for {self._base_url}")
            await self._session.close()
            self._session = None

    def __del__(self):
        """Cleanup session on object destruction."""
        if self._session and not self._session.closed:
            try:
                # Try to close session, but don't fail if event loop is closed
                loop = asyncio.get_event_loop()
                if loop and not loop.is_closed():
                    loop.create_task(self.close_async())
            except:
                pass  # Ignore errors during cleanup
