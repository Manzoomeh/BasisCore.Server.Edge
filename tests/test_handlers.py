"""Handler registration and dispatch_async coverage."""
from bclib.context import (
    HttpContext,
    RabbitContext,
    RESTfulContext,
    WebSocketContext,
)
from bclib.listener.rabbit.rabbit_message import RabbitMessage
from bclib.utility import HttpBaseDataName, HttpBaseDataType

from helpers import cms_content, http_context, make_cms, run_dispatch, ws_text_message


def test_restful_handler_dispatches(app):
    @app.restful_handler("api/hello", method="GET")
    def hello(context: RESTfulContext):
        return {"ok": True, "url": context.url}

    cms = make_cms(url="api/hello", method="get")
    result = run_dispatch(app, http_context(app, cms, RESTfulContext))
    assert cms_content(result) == {"ok": True, "url": "api/hello"}


def test_restful_handler_url_segments(app):
    @app.restful_handler("api/users/:id", method="GET")
    def get_user(context: RESTfulContext):
        return {"id": context.url_segments["id"]}

    cms = make_cms(url="api/users/42", method="get")
    result = run_dispatch(app, http_context(app, cms, RESTfulContext))
    assert cms_content(result) == {"id": "42"}


def test_web_handler_dispatches(app):
    @app.web_handler("home", method="GET")
    def home(context: HttpContext):
        return "<h1>home</h1>"

    cms = make_cms(url="home", method="get")
    result = run_dispatch(app, http_context(app, cms, HttpContext))
    content = result[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT]
    assert "<h1>home</h1>" in str(content)


def test_universal_handler_routes_by_context_type(app):
    @app.handler("auto", method="GET")
    def auto(context: RESTfulContext):
        return {"mode": "auto"}

    cms = make_cms(url="auto", method="get")
    result = run_dispatch(app, http_context(app, cms, RESTfulContext))
    assert cms_content(result) == {"mode": "auto"}


def test_rabbit_handler_dispatches(app):
    @app.rabbit_handler()
    def on_rabbit(context: RabbitContext):
        return {"queue": context.queue, "body": context.raw_message}

    message = RabbitMessage(
        host="localhost",
        queue="tasks",
        body=b'{"job":1}',
        routing_key="task.run",
    )
    result = run_dispatch(app, RabbitContext({}, app, message))
    assert result == {"queue": "tasks", "body": '{"job":1}'}


def test_websocket_handler_dispatches(app):
    @app.websocket_handler("ws/chat")
    def on_ws(context: WebSocketContext):
        return {"sid": context.session.id, "text": context.message.text}

    cms = make_cms(url="ws/chat")
    msg = ws_text_message(cms)
    result = run_dispatch(app, WebSocketContext(cms, app, msg))
    assert result["sid"] == "sess-test-12345678"
    assert result["text"] == "hello"


def test_handler_not_found_error_response(app):
    cms = make_cms(url="missing-route", method="get")
    ctx = http_context(app, cms, RESTfulContext)
    result = run_dispatch(app, ctx)
    assert result is not None
    assert HttpBaseDataType.CMS in result
