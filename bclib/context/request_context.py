import json
from typing import TYPE_CHECKING, Any

from bclib.context.context import Context
from bclib.exception import ShortCircuitErr
from bclib.utility import HttpMimeTypes, HttpStatusCodes, ResponseTypes

if TYPE_CHECKING:
    from .. import dispatcher


class RequestContext(Context):
    """Base class for dispatching http base request context"""

    def __init__(self, cms_object: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(dispatcher)
        self.cms = cms_object
        self.url: str = self.cms.get('request', {}).get('url')
        self.query: dict = self.cms.get('query', {})
        self.form: dict = self.cms.get('form', {})
        self.__headers: dict = None
        self.response_type: str = ResponseTypes.RENDERED
        self.status_code: str = HttpStatusCodes.OK
        self.mime = HttpMimeTypes.HTML

    def add_header(self, key: str, value: str) -> None:
        """Adding item to response header"""

        if self.__headers is None:
            self.__headers = dict()
        if key not in self.__headers:
            self.__headers[key] = [value]
        else:
            self.__headers[key].append(value)

    def generate_error_response(self, exception: Exception) -> dict:
        """Generate error response from process result"""
        error_object, self.status_code = self._generate_error_object(exception)
        if isinstance(exception, ShortCircuitErr) and exception.data:
            content = exception.data if isinstance(
                exception.data, str) else json.dumps(exception.data, indent=1).replace("\n", "</br>")
        else:
            content = f"{error_object['errorMessage']} (Error Code: {error_object['errorCode']})"
            if 'error' in error_object:
                error = error_object["error"].replace("\n", "</br>")
                content += f"<hr/>{error}"
        self.mime = HttpMimeTypes.HTML
        return self.generate_response(content)

    def generate_response(self, content: Any) -> dict:
        """Generate response from process result"""

        return Context._generate_response_cms(content, self.response_type, self.status_code, self.mime, self.cms, self.__headers)
