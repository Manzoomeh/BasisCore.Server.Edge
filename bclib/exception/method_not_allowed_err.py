from bclib.exception.short_circuit_err import ShortCircuitErr
from bclib.utility.http_status_codes import HttpStatusCodes


class MethodNotAllowedErr(ShortCircuitErr):
    def __init__(self, message: str = None, data: 'dict' = None):
        super().__init__(HttpStatusCodes.METHOD_NOT_ALLOWED, 'http-405', message, data)
