"""
RESTful Context - Context for RESTful API requests

This module provides the RESTfulContext class for handling RESTful API requests in the BasisCore.Server.Edge framework.
It extends HttpContext to provide JSON-based request/response handling with automatic body parsing
and RESTful conventions.

Key Features:
    - Automatic JSON request body parsing
    - Support for application/json and application/x-www-form-urlencoded content types
    - JSON response generation
    - RESTful error handling with proper status codes
    - Inherits all HTTP streaming and compression capabilities

Example:
    ```python
    @app.restful_action(app.url("api/users"))
    async def create_user(context: RESTfulContext):
        # Access parsed JSON body
        user_data = context.body
        
        # Create user
        user = await create_user_in_db(user_data)
        
        # Return JSON response
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
        
    @app.restful_action(app.url("api/users/{id}"))
    async def get_user(context: RESTfulContext):
        user_id = context.url_segments.get('id')
        user = await get_user_from_db(user_id)
        
        if not user:
            raise NotFoundException(f"User {user_id} not found")
            
        return user.to_dict()
    ```
"""
import json
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl

from bclib.context.http_context import HttpContext
from bclib.utility.http_mime_types import HttpMimeTypes

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.listener.http.http_message import HttpMessage


class RESTfulContext(HttpContext):
    """
    Context class for RESTful API requests

    Provides RESTful API-specific functionality with automatic JSON handling,
    body parsing for multiple content types, and standardized response generation.

    Attributes:
        mime (str): MIME type for response, set to application/json by default
        body (dict|None): Parsed request body (JSON or form data)

    Args:
        cms_object: CMS object containing request data
        dispatcher: Dispatcher instance for routing and handling
        message_object: HTTP message object from the listener

    Note:
        The constructor automatically parses request body based on Content-Type:
        - application/json: Parses as JSON
        - application/x-www-form-urlencoded: Parses as form data
        - Other types: Falls back to form data from CMS object
    """

    def __init__(self, cms_object: dict, dispatcher: 'IDispatcher', message_object: 'HttpMessage') -> None:
        super().__init__(cms_object, dispatcher, message_object)
        self.mime = HttpMimeTypes.JSON
        temp_data = None

        # First priority: Check if form data exists in CMS object
        if self.form:
            temp_data = self.form
        else:
            # Second priority: Parse request body based on content type
            request: dict = self.cms.get('request', {})
            body = request.get('body')
            if body:
                content_type: str | None = request.get('content-type')

                # Handle URL-encoded form data
                if content_type and content_type.find("x-www-form-urlencoded") > -1:
                    temp_data = dict()
                    for key, value in parse_qsl(body):
                        temp_data[key.strip()] = value

                # Handle JSON data
                elif content_type and content_type.find("json") > -1:
                    try:
                        temp_data = json.loads(body)
                    except Exception as ex:
                        print('error in extract request body', ex)

        self.body = temp_data

    def generate_error_response(self,  exception: Exception) -> dict:
        """
        Generate JSON error response from exception

        Converts an exception into a properly formatted JSON error response
        with appropriate HTTP status code.

        Args:
            exception: The exception that occurred during request processing

        Returns:
            dict: JSON string containing error information

        Example:
            ```python
            # Framework automatically calls this on exceptions
            # Result format:
            {
                "errorCode": "404",
                "errorMessage": "User not found"
            }
            ```

        Note:
            This method automatically sets the appropriate status_code and mime type.
            The status code is determined by the exception type (e.g., NotFoundException -> 404).
        """
        error_object, self.status_code = self._generate_error_object(exception)
        return self.generate_response(error_object)
