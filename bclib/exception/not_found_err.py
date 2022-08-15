from bclib.utility.http_status_codes import HttpStatusCodes
from ..exception.short_circuit_err import ShortCircuitErr


class NotFoundErr(ShortCircuitErr):
    def __init__(self, message: str = None, data: 'dict' = None):
        super().__init__(HttpStatusCodes.NOT_FOUND, 'http-404', message, data)
