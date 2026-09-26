"""Context construction coverage."""

from bclib.context import (
    ClientSourceContext,
    HttpContext,
    RabbitContext,
    RESTfulContext,
    ServerSourceContext,
    WebSocketContext,
)
from bclib.listener.http.http_message import HttpMessage
from bclib.listener.rabbit.rabbit_message import RabbitMessage

from helpers import make_cms, ws_text_message


def test_restful_and_http_context(app):
    cms = make_cms(url="api/x", body='{"a":1}')
    msg = HttpMessage(cms)
    rest = RESTfulContext(cms, app, msg)
    http = HttpContext(cms, app, msg)

    assert rest.url == "api/x"
    assert http.url == "api/x"
    assert rest.services is not None


def test_rabbit_context(app):
    message = RabbitMessage("host1", "q1", b"payload")
    ctx = RabbitContext({}, app, message)

    assert ctx.host == "host1"
    assert ctx.queue == "q1"
    assert ctx.raw_message == "payload"
    assert ctx.message is message


def test_websocket_context(app):
    cms = make_cms(url="ws/room")
    msg = ws_text_message(cms)
    ctx = WebSocketContext(cms, app, msg)

    assert ctx.session.id.startswith("sess-")
    assert ctx.message.text == "hello"
    assert ctx.session_manager is msg.session.session_manager


def test_client_source_context_parses_command(app):
    cms = make_cms(
        form={
            "command": '<basis core="dbSource"><params><add name="x" value="1"/></params></basis>',
            "dmnid": "9",
        }
    )
    ctx = ClientSourceContext(cms, app, HttpMessage(cms))
    assert ctx.dmn_id == "9"
    assert ctx.command is not None
    assert ctx.params is None or isinstance(ctx.params, dict)


def test_server_source_context_parses_command(app):
    cms = {
        "command": '<basis core="dbSource"></basis>',
        "dmnid": "3",
        "params": {"a": 1},
    }
    ctx = ServerSourceContext(cms, app)
    assert ctx.dmn_id == "3"
    assert ctx.params == {"a": 1}
    assert ctx.generate_response({"ok": True}) == {"ok": True}
