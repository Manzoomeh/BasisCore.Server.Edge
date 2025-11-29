"""
CMS Base Context - Base class for CMS-based request contexts

This module provides the CmsBaseContext class that serves as the foundation for all
CMS (Content Management System) protocol contexts in the BasisCore.Server.Edge framework.
It extends the base Context class with CMS-specific functionality including URL handling,
query/form data parsing, response generation, and error handling.

Key Features:
    - CMS object parsing (request, query, form data)
    - URL segment extraction for routing parameters
    - Response type management (HTML, JSON, file downloads)
    - HTTP status code and MIME type handling
    - Custom header management
    - Standardized error response generation
    - BasisCore CMS format response wrapping

Example:
    ```python
    # CmsBaseContext is typically not used directly
    # Instead, use derived classes like HttpContext or RESTfulContext
    
    @app.http_action(app.url("page/{page_id}"))
    async def serve_page(context: HttpContext):
        # Access parsed data from CMS object
        page_id = context.url_segments.get('page_id')
        query_param = context.query.get('filter')
        form_data = context.form.get('user_input')
        
        # Add custom headers
        context.add_header('X-Custom-Header', 'value')
        
        # Generate response
        return context.generate_response("<h1>Page Content</h1>")
    ```
    
Note:
    This is an intermediate base class. Use protocol-specific contexts like
    HttpContext, RESTfulContext, WebSocketContext, or TcpContext in your handlers.
"""
import json
import traceback
from typing import TYPE_CHECKING, Any, Tuple

from bclib.context.context import Context
from bclib.exception.short_circuit_err import ShortCircuitErr

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher

from bclib.utility.http_base_data_name import HttpBaseDataName
from bclib.utility.http_base_data_type import HttpBaseDataType
from bclib.utility.http_mime_types import HttpMimeTypes
from bclib.utility.http_status_codes import HttpStatusCodes
from bclib.utility.response_types import ResponseTypes


class CmsBaseContext(Context):
    """
    Base class for CMS-based request contexts

    Provides CMS-specific functionality including request data parsing, response generation,
    and error handling for HTTP-based protocols. All CMS contexts (HTTP, RESTful, WebSocket)
    inherit from this class.

    Attributes:
        url_segments (dict): URL parameters extracted from route patterns (e.g., {id} → url_segments['id'])
        cms (dict): The complete CMS object containing all request data
        url (str): The request URL path
        query (dict): Query string parameters parsed into dictionary
        form (dict): Form data from POST requests
        response_type (str): Type of response (RENDERED, FILE, etc.)
        status_code (str): HTTP status code for the response
        mime (str): MIME type for the response content

    Args:
        cms_object: CMS object containing request, query, form, and other data
        dispatcher: Dispatcher instance for routing and DI
        create_scope: Whether to create a new DI scope for this request

    Example:
        ```python
        # CmsBaseContext is the parent of HttpContext, RESTfulContext, etc.
        # You typically work with derived classes

        @app.http_action(app.url("users/{user_id}/posts/{post_id}"))
        async def get_user_post(context: HttpContext):
            # Access URL segments
            user_id = context.url_segments['user_id']
            post_id = context.url_segments['post_id']

            # Access query parameters
            include_comments = context.query.get('comments', 'false') == 'true'

            # Set response properties
            context.mime = HttpMimeTypes.JSON
            context.status_code = HttpStatusCodes.OK

            return {"user_id": user_id, "post_id": post_id}
        ```
    """

    # 1. Constructor
    def __init__(self, cms_object: dict,  dispatcher: 'IDispatcher', create_scope: bool) -> None:
        """
        Initialize CMS base context

        Args:
            cms_object: CMS object with request data structure
            dispatcher: Dispatcher instance for routing
            create_scope: If True, creates new DI scope

        Note:
            Automatically parses URL, query, and form data from cms_object.
            Sets default response type to RENDERED and status code to OK.
        """
        super().__init__(dispatcher, create_scope)
        self.url_segments: dict[str, str] = None
        self.cms = cms_object
        self.url: str = self.cms.get('request', {}).get('url')
        self.query: dict[str, str] = self.cms.get('query', {})
        self.form: dict[str, str] = self.cms.get('form', {})
        self.methode: str = self.cms.get('request', {}).get('methode')
        self.__headers: dict[str, list[str]] = None
        self.response_type: str = ResponseTypes.RENDERED
        self.status_code: str = HttpStatusCodes.OK
        self.mime = HttpMimeTypes.HTML

    # 2. Public methods
    def add_header(self, key: str, value: str) -> None:
        """
        Add custom header to response

        Adds a custom HTTP header to the response. Headers can have multiple values
        for the same key.

        Args:
            key: Header name (e.g., 'Content-Type', 'X-Custom-Header')
            value: Header value

        Example:
            ```python
            context.add_header('Cache-Control', 'no-cache')
            context.add_header('X-Request-ID', request_id)
            context.add_header('Set-Cookie', 'session=abc123')
            context.add_header('Set-Cookie', 'user=john')  # Multiple values
            ```
        """
        if self.__headers is None:
            self.__headers = dict()
        if key not in self.__headers:
            self.__headers[key] = [value]
        else:
            self.__headers[key].append(value)

    def generate_error_response(self, exception: Exception) -> dict:
        """
        Generate HTML error response from exception

        Converts an exception into an HTML-formatted error response with appropriate
        HTTP status code. Handles ShortCircuitErr exceptions specially to preserve
        custom error data and status codes.

        Args:
            exception: The exception that occurred during request processing

        Returns:
            dict: CMS-formatted response object with HTML error content

        Example:
            ```python
            # Framework automatically calls this on exceptions
            # Result is HTML formatted error page:
            # <error_message> (Error Code: <code>)
            # <hr/>
            # <stack_trace_if_debug_mode>
            ```

        Note:
            Sets mime type to HTML and status_code based on exception type.
            For ShortCircuitErr, preserves the exception's status code and data.
        """
        error_object, self.status_code = self._generate_error_object(exception)
        if isinstance(exception, ShortCircuitErr) and exception.data:
            content = exception.data if isinstance(
                exception.data, str) else json.dumps(exception.data, indent=1).replace("\n", "</br>")
        else:
            content = f"{error_object['errorMessage']} (Error Code: {error_object['errorCode']})"
            if 'error' in error_object:
                error = error_object["error"].replace("\n", "</br>")
                content += f"<hr/>{error}"
        return self.generate_response(content)

    def generate_response(self, content: Any) -> dict:
        """
        Generate CMS-formatted response

        Wraps content into BasisCore CMS response format with appropriate headers,
        status codes, and MIME types.

        Args:
            content: Response content (string, bytes, or any serializable object)

        Returns:
            dict: CMS-formatted response object ready for transmission

        Example:
            ```python
            # String content
            return context.generate_response("<h1>Hello World</h1>")

            # Bytes content (e.g., file download)
            context.mime = HttpMimeTypes.PDF
            return context.generate_response(pdf_bytes)
            ```

        Note:
            Automatically includes custom headers added via add_header().
            Response structure follows BasisCore CMS specification.
        """
        response_cms = self.cms
        if HttpBaseDataType.CMS not in response_cms:
            response_cms[HttpBaseDataType.CMS] = {}
        if HttpBaseDataName.WEB_SERVER not in response_cms[HttpBaseDataType.CMS]:
            response_cms[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER] = {}
        response_cms[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.INDEX] = self.response_type
        response_cms[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.HEADER_CODE] = self.status_code
        response_cms[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.MIME] = self.mime
        if isinstance(content, bytes):
            response_cms[HttpBaseDataType.CMS][HttpBaseDataName.BLOB_CONTENT] = content
        else:
            response_cms[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT] = content if isinstance(
                content, str) else json.dumps(content)
        if self.__headers is not None:
            CmsBaseContext.__add_user_defined_headers(
                response_cms, self.__headers)
        return response_cms

    # 3. Private methods
    def _generate_error_object(self, exception: Exception) -> 'Tuple[dict, str]':
        """
        Generate error object from exception

        Creates a standardized error object with error code, message, and optional
        stack trace. Handles ShortCircuitErr exceptions specially.

        Args:
            exception: The exception to convert to error object

        Returns:
            Tuple[dict, str]: Error object dict and HTTP status code

        Note:
            Includes stack trace if dispatcher.logger.log_error is enabled.
            For ShortCircuitErr, uses exception's custom data and status code.
        """
        error_code = None
        data = None
        status_code = HttpStatusCodes.INTERNAL_SERVER_ERROR
        if isinstance(exception, ShortCircuitErr):
            data = exception.data
            status_code = exception.status_code
            error_code = exception.error_code
        if data:
            error_object = data
        else:
            error_object = {
                "errorCode": error_code,
                "errorMessage": str(exception)
            }
            if self.dispatcher.logger.log_error:
                error_object["error"] = traceback.format_exc()
        return (error_object, status_code)

    # 4. Static methods
    @staticmethod
    def __add_user_defined_headers(cms: dict, headers: dict) -> None:
        """
        Add user-defined headers to CMS response

        Internal method to merge custom headers into CMS response structure.
        Handles multiple values for the same header key.

        Args:
            cms: CMS response object to modify
            headers: Dictionary of headers to add

        Note:
            Multiple header values are joined with commas as per HTTP spec.
            This is a private static method for internal use only.
        """
        if HttpBaseDataName.HTTP not in cms[HttpBaseDataType.CMS]:
            cms[HttpBaseDataType.CMS][HttpBaseDataName.HTTP] = {}
        http = cms[HttpBaseDataType.CMS][HttpBaseDataName.HTTP]
        for key, value in headers.items():
            if key in http:
                current_value = http[key] if isinstance(
                    http[key], list) else [http[key]]
                new_value = current_value + value
            else:
                new_value = value

            http[key] = ",".join(new_value)
