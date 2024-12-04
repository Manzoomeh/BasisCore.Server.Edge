from abc import ABC
import traceback
import base64
from typing import TYPE_CHECKING, Optional, Tuple

from bclib.exception import ShortCircuitErr
from bclib.utility import DictEx, HttpStatusCodes, HttpStatusCodes
from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher


class Context(ABC):
    """Base class for dispatching"""

    def __init__(self, dispatcher: 'IDispatcher') -> None:
        super().__init__()
        self.dispatcher = dispatcher
        self.url_segments: DictEx = None
        self.url: Optional[str] = None
        self.is_adhoc = True

    #TODO:Removed wrapper open_X_connection methode 

    def generate_error_response(self, exception: Exception) -> dict:
        """Generate error response from process result"""

        error_object, _ = self._generate_error_object(exception)
        return error_object

    def _generate_error_object(self, exception: Exception) -> 'Tuple[dict, str]':
        """Generate error object from exception object"""
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
            #TODO:use logger service
            if True:#self.dispatcher.log_error:
                error_object["error"] = traceback.format_exc()
        return (error_object, status_code)

    @staticmethod
    def _generate_response_cms(
            content: 'str|bytes',
            response_type: 'str',
            status_code: 'str',
            mime: 'str',
            template: 'DictEx' = None,
            headers: 'dict' = None) -> dict:
        """Generate response from process result"""

        ret_val = DictEx() if template is None else template
        if HttpBaseDataType.CMS not in ret_val:
            ret_val[HttpBaseDataType.CMS] = {}
        if HttpBaseDataName.WEB_SERVER not in ret_val[HttpBaseDataType.CMS]:
            ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER] = DictEx()
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.INDEX] = response_type
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.HEADER_CODE] = status_code
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER][HttpBaseDataName.MIME] = mime
        if isinstance(content,bytes):
            ret_val[HttpBaseDataType.CMS][HttpBaseDataName.BLOB_CONTENT] = base64.b64encode(content).decode("utf-8")  
        else:
            ret_val[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT] = content
        if headers is not None:
            Context.__add_user_defined_headers(ret_val, headers)
        return ret_val

    @staticmethod
    def __add_user_defined_headers(response: dict, headers: dict) -> None:
        """Adding user defined header to response"""

        if HttpBaseDataName.HTTP not in response[HttpBaseDataType.CMS]:
            response[HttpBaseDataType.CMS][HttpBaseDataName.HTTP] = {}
        http = response[HttpBaseDataType.CMS][HttpBaseDataName.HTTP]
        for key, value in headers.items():
            if key in http:
                current_value = http[key] if isinstance(
                    http[key], list) else [http[key]]
                new_value = current_value + value
            else:
                new_value = value

            http[key] = ",".join(new_value)
