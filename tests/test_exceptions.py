"""Exception hierarchy coverage."""
from bclib.exception import (
    BadRequestErr,
    ForbiddenErr,
    HandlerNotFoundErr,
    InternalServerErr,
    MethodNotAllowedErr,
    NotFoundErr,
    ShortCircuitErr,
    UnauthorizedErr,
)
from bclib.utility.http_status_codes import HttpStatusCodes


def test_short_circuit_base():
    err = ShortCircuitErr("418", error_code="x", message="teapot", data={"a": 1})
    assert err.status_code == "418"
    assert err.error_code == "x"
    assert str(err) == "teapot"
    assert err.data == {"a": 1}


def test_http_error_subclasses():
    assert BadRequestErr().status_code == HttpStatusCodes.BAD_REQUEST
    assert UnauthorizedErr().status_code == HttpStatusCodes.UNAUTHORIZED
    assert ForbiddenErr().status_code == HttpStatusCodes.FORBIDDEN
    assert NotFoundErr().status_code == HttpStatusCodes.NOT_FOUND
    assert MethodNotAllowedErr().status_code == HttpStatusCodes.METHOD_NOT_ALLOWED
    assert InternalServerErr().status_code == HttpStatusCodes.INTERNAL_SERVER_ERROR


def test_handler_not_found_is_not_found():
    err = HandlerNotFoundErr("RESTfulContext")
    assert isinstance(err, NotFoundErr)
    assert err.status_code == HttpStatusCodes.NOT_FOUND
    assert "RESTfulContext" in str(err)
