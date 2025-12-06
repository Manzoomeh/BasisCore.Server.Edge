"""
URL Predicate Module

Provides URL pattern matching and parameter extraction predicate for routing.

Features:
    - URL pattern matching with parameter extraction
    - Dynamic segment parsing (e.g., /users/:id)
    - Wildcard segment support (e.g., /files/:*path)
    - Case-insensitive matching
    - Automatic url_segments population

Example:
    ```python
    from bclib.predicate import Url
    
    # Match /users/123 and extract id
    predicate = Url("/users/:id")
    
    # Match /files/path/to/resource with wildcard
    file_predicate = Url("/files/:*path")
    ```
"""

from types import FunctionType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.context.cms_base_context import CmsBaseContext

from .predicate import Predicate


class Url(Predicate):
    """
    URL pattern matching predicate

    Matches request URLs against patterns and extracts URL parameters.
    Supports dynamic segments (prefixed with :) and wildcard segments (:*).

    Args:
        expression: URL pattern with optional parameters (e.g., "/users/:id" or "/files/:*path")

    Example:
        ```python
        # Simple static URL
        home = Url("/")

        # URL with parameter
        user_detail = Url("/users/:id")
        # Matches: /users/123, extracts id="123"

        # URL with multiple parameters
        post = Url("/users/:user_id/posts/:post_id")
        # Matches: /users/42/posts/100

        # Wildcard parameter (captures rest of path)
        files = Url("/files/:*path")
        # Matches: /files/documents/report.pdf
        # Extracts: path="documents/report.pdf"

        @app.handler(route=Url("/api/users/:id"))
        async def get_user(context):
            user_id = context.url_segments['id']
        ```
    """

    def __init__(self, expression: str) -> None:
        """
        Initialize URL pattern predicate

        Args:
            expression: URL pattern with optional :param or :*param segments

        Note:
            URL validator is generated and compiled once during initialization.
        """
        super().__init__(expression)
        self.__validator: FunctionType = Url.__generate_validator(expression)

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if request URL matches pattern

        Args:
            context: Current request context (must be CmsBaseContext)

        Returns:
            True if URL matches pattern, False otherwise

        Raises:
            Does not raise exceptions; returns False on error

        Note:
            On successful match, extracts URL parameters into context.url_segments
        """
        try:
            if isinstance(context, CmsBaseContext):
                is_ok, url_parts = self.__validator(context.url)
                if is_ok and url_parts:
                    context.url_segments = url_parts
                return is_ok
            else:
                return False
        except Exception as ex:
            print("Error in check url predicate", ex)
            return False

    @staticmethod
    def __generate_validator(url: str) -> FunctionType:
        """
        Generate dynamic URL validator function

        Creates a compiled function that efficiently validates URLs against
        the pattern and extracts parameters.

        Args:
            url: URL pattern string

        Returns:
            Compiled function that takes a URL and returns (is_match, params_dict)

        Note:
            Uses Python compile() and FunctionType for runtime code generation.
            Segments starting with : are parameters, :* captures remaining path.
        """
        segment_list = []
        return_dict_property_names = []
        where_part_list = []
        parts = url.split("/")
        last_part_index = len(parts) - 1

        for index, value in enumerate(parts):
            name = "_"
            if len(value) > 0 and value[0] == ':':
                name = value[1:]
                if index == last_part_index and name[0] == '*':
                    # Wildcard parameter (captures remaining path)
                    name = name[1:]
                    return_dict_property_names.append(
                        f'"{name}" : "/".join(__{name})')
                    name = f"*__{name}"
                else:
                    # Regular parameter
                    return_dict_property_names.append(
                        f'"{name}" : __{name}')
                    name = f"__{name}"
            else:
                # Static segment
                where_part_list.append(
                    f"url_parts[{index}].lower() == '{value.lower()}'")
            segment_list.append(name)

        if len(where_part_list) == 0:
            if len(return_dict_property_names) == 0:
                where_part_list.append("True")
            else:
                where_part_list.append(
                    f"len(url_parts) == {len(return_dict_property_names)}")
                if len(return_dict_property_names) == 1:
                    where_part_list.append("len(url_parts[0]) > 0")

        if len(return_dict_property_names) > 0:
            body = f"""
def url_function(url):
    try:
        url_parts = url.split("/")
        if {" and ".join(where_part_list)}:
            {','.join(segment_list)} = url_parts{"[0]" if len(segment_list) == 1 else ""}
            return (True,{{ {','.join(return_dict_property_names)} }})
        else:
            return (False,None)
    except Exception as e:
        return (False,None)"""
        else:
            body = f"""
def url_function(url):
    return (url.lower() == '{url.lower()}' ,None)"""

        f_code = compile(body, "<str>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), "url_function")
        return f_func
