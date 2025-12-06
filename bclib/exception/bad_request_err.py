from bclib.exception.short_circuit_err import ShortCircuitErr
from bclib.utility.http_status_codes import HttpStatusCodes


class BadRequestErr(ShortCircuitErr):
    def __init__(self, message: str = None, data: 'dict' = None):
        super().__init__(HttpStatusCodes.BAD_REQUEST, 'http-400', message, data)
