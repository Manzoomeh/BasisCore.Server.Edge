"""RESTful HTTP Connection - Enhanced with certifi and raise_for_status"""
import asyncio
import ssl
from typing import Any, Dict, Generic, Optional, TypeVar

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from bclib.logger.ilogger import ILogger
from bclib.options import IOptions

from .irestful_connection import IRestfulConnection

T = TypeVar('T')


class RestfulConnection(IRestfulConnection[T], Generic[T]):
    """
    RESTful HTTP Connection - Enhanced async HTTP client.

    Features:
        - Async HTTP methods (GET, POST, PUT, PATCH, DELETE)
        - Automatic JSON/text parsing
        - HTTP error handling with raise_for_status
        - SSL verification with certifi CA bundle
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
                },
                "ssl_verify": true,
                "ssl_cert_path": "/path/to/cert.pem"
            }
        }
        ```

    Usage:
        ```python
        class UserService:
            def __init__(self, api: IRestfulConnection['external_api']):
                self.api = api

            async def get_users(self):
                # Automatically parses JSON and raises for HTTP errors
                return await self.api.get_async('/users')

            async def create_user(self, name: str):
                return await self.api.post_async('/users', json={'name': name})

            async def create_user_no_error_check(self, name: str):
                # Disable automatic error checking
                return await self.api.post_async(
                    '/users', 
                    json={'name': name},
                    raise_for_status=False
                )
        ```
    """

    def __init__(
        self,
        options: IOptions['RestfulConnection[T]'],
        logger: Optional[ILogger['RestfulConnection[T]']] = None
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
        self._ssl_verify = self._options.get('ssl_verify', True)
        self._ssl_cert_path = self._options.get('ssl_cert_path', None)

        if not self._base_url:
            raise ValueError(
                f"Configuration key '{options.key}' must contain 'base_url'")

        # Create SSL context
        self._ssl_context = self._create_ssl_context()

        if self._logger:
            ssl_status = "with certifi" if self._ssl_verify and not self._ssl_cert_path else (
                "with custom cert" if self._ssl_cert_path else "disabled")
            self._logger.info(
                f"RestfulConnection initialized: {self._base_url} (SSL {ssl_status})")

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context with certifi CA bundle.

        Uses certifi for reliable cross-platform SSL verification.
        This fixes CERTIFICATE_VERIFY_FAILED errors on Windows/venv
        where OpenSSL default CA paths may be missing.

        Returns:
            SSLContext object, False to disable SSL, or None for default
        """
        if not self._ssl_verify:
            # Disable SSL verification
            if self._logger:
                self._logger.warning(
                    "SSL certificate verification is DISABLED. Use only in development!")
            return False

        if self._ssl_cert_path:
            # Use custom CA certificate
            ssl_context = ssl.create_default_context(
                cafile=self._ssl_cert_path)
            if self._logger:
                self._logger.info(
                    f"Using custom SSL certificate: {self._ssl_cert_path}")
            return ssl_context

        # Use certifi CA bundle for reliable cross-platform SSL
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            if self._logger:
                self._logger.debug(
                    "Using certifi CA bundle for SSL verification")
            return ssl_context
        except ImportError:
            if self._logger:
                self._logger.warning(
                    "certifi not installed, using default SSL. "
                    "Install with: pip install certifi")
            # Fall back to default SSL
            return None

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
        Get or create aiohttp ClientSession with connection pooling.

        Returns:
            Active ClientSession instance
        """
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    timeout = ClientTimeout(total=self._timeout)

                    # Configure SSL connector
                    if self._ssl_context is False:
                        # Disable SSL
                        connector = TCPConnector(ssl=False)
                    elif self._ssl_context:
                        # Use custom SSL context (certifi or custom cert)
                        connector = TCPConnector(ssl=self._ssl_context)
                    else:
                        # Use default SSL
                        connector = TCPConnector(ssl=True)

                    self._session = ClientSession(
                        base_url=self._base_url,
                        timeout=timeout,
                        headers=self._default_headers,
                        connector=connector
                    )

                    if self._logger:
                        self._logger.debug(
                            f"Created new ClientSession for {self._base_url}")

        return self._session

    async def _read_response_async(self, response: ClientResponse) -> Any:
        """
        Read response with JSON/text fallback.

        Tries to parse as JSON first, falls back to text if parsing fails.
        This handles APIs that don't set proper content-type headers.

        Args:
            response: aiohttp ClientResponse

        Returns:
            Parsed JSON (dict/list) or text string
        """
        try:
            # Try JSON first regardless of content-type
            return await response.json()
        except Exception:
            # Fall back to text for non-JSON responses
            return await response.text()

    async def get_async(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = True
    ) -> Any:
        """
        Perform HTTP GET request.

        Args:
            path: API endpoint path (relative to base_url)
            params: URL query parameters
            headers: Additional request headers
            raise_for_status: Raise exception if status >= 400 (default: True)

        Returns:
            Parsed JSON or text content

        Raises:
            Exception: If request fails or status >= 400 (when raise_for_status=True)
        """
        session = await self.get_session_async()
        # Session already has base_url, so just use the path
        path = path.lstrip('/')

        try:
            async with session.get(path, params=params, headers=headers) as response:
                # Check for HTTP errors
                if raise_for_status and response.status >= 400:
                    error_body = await self._read_response_async(response)
                    raise Exception(
                        f"GET failed: status={response.status} url={path} response={error_body}")

                if self._logger:
                    self._logger.debug(
                        f"GET {path} - Status: {response.status}")

                return await self._read_response_async(response)

        except Exception as e:
            if self._logger:
                self._logger.error(f"GET error: {path} - {str(e)}")
            raise

    async def post_async(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = True
    ) -> Any:
        """
        Perform HTTP POST request.

        Args:
            path: API endpoint path (relative to base_url)
            data: Form data to send
            json: JSON data to send
            headers: Additional request headers
            raise_for_status: Raise exception if status >= 400 (default: True)

        Returns:
            Parsed JSON or text content

        Raises:
            Exception: If request fails or status >= 400 (when raise_for_status=True)
        """
        session = await self.get_session_async()
        path = path.lstrip('/')

        try:
            async with session.post(path, data=data, json=json, headers=headers) as response:
                # Check for HTTP errors
                if raise_for_status and response.status >= 400:
                    error_body = await self._read_response_async(response)
                    raise Exception(
                        f"POST failed: status={response.status} url={path} response={error_body}")

                if self._logger:
                    self._logger.debug(
                        f"POST {path} - Status: {response.status}")

                return await self._read_response_async(response)

        except Exception as e:
            if self._logger:
                self._logger.error(f"POST error: {path} - {str(e)}")
            raise

    async def put_async(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = True
    ) -> Any:
        """
        Perform HTTP PUT request.

        Args:
            path: API endpoint path (relative to base_url)
            data: Form data to send
            json: JSON data to send
            headers: Additional request headers
            raise_for_status: Raise exception if status >= 400 (default: True)

        Returns:
            Parsed JSON or text content

        Raises:
            Exception: If request fails or status >= 400 (when raise_for_status=True)
        """
        session = await self.get_session_async()
        path = path.lstrip('/')

        try:
            async with session.put(path, data=data, json=json, headers=headers) as response:
                # Check for HTTP errors
                if raise_for_status and response.status >= 400:
                    error_body = await self._read_response_async(response)
                    raise Exception(
                        f"PUT failed: status={response.status} url={path} response={error_body}")

                if self._logger:
                    self._logger.debug(
                        f"PUT {path} - Status: {response.status}")

                return await self._read_response_async(response)

        except Exception as e:
            if self._logger:
                self._logger.error(f"PUT error: {path} - {str(e)}")
            raise

    async def patch_async(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = True
    ) -> Any:
        """
        Perform HTTP PATCH request.

        Args:
            path: API endpoint path (relative to base_url)
            data: Form data to send
            json: JSON data to send
            headers: Additional request headers
            raise_for_status: Raise exception if status >= 400 (default: True)

        Returns:
            Parsed JSON or text content

        Raises:
            Exception: If request fails or status >= 400 (when raise_for_status=True)
        """
        session = await self.get_session_async()
        path = path.lstrip('/')

        try:
            async with session.patch(path, data=data, json=json, headers=headers) as response:
                # Check for HTTP errors
                if raise_for_status and response.status >= 400:
                    error_body = await self._read_response_async(response)
                    raise Exception(
                        f"PATCH failed: status={response.status} url={path} response={error_body}")

                if self._logger:
                    self._logger.debug(
                        f"PATCH {path} - Status: {response.status}")

                return await self._read_response_async(response)

        except Exception as e:
            if self._logger:
                self._logger.error(f"PATCH error: {path} - {str(e)}")
            raise

    async def delete_async(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = True
    ) -> Any:
        """
        Perform HTTP DELETE request.

        Args:
            path: API endpoint path (relative to base_url)
            params: URL query parameters
            headers: Additional request headers
            raise_for_status: bool = True)

        Returns:
            Parsed JSON or text content

        Raises:
            Exception: If request fails or status >= 400 (when raise_for_status=True)
        """
        session = await self.get_session_async()
        path = path.lstrip('/')

        try:
            async with session.delete(path, params=params, headers=headers) as response:
                # Check for HTTP errors
                if raise_for_status and response.status >= 400:
                    error_body = await self._read_response_async(response)
                    raise Exception(
                        f"DELETE failed: status={response.status} url={path} response={error_body}")

                if self._logger:
                    self._logger.debug(
                        f"DELETE {path} - Status: {response.status}")

                return await self._read_response_async(response)

        except Exception as e:
            if self._logger:
                self._logger.error(f"DELETE error: {path} - {str(e)}")
            raise

    async def close_async(self) -> None:
        """
        Close the HTTP session and release resources.

        Call this when the connection is no longer needed.
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
