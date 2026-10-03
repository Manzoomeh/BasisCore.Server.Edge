"""A request that fails before a handler can reply still gets an error response.

Without a reply the BasisCore web server only sees a closed connection and reports an
unrelated error (ArgumentNullException in FromSocketResultToRoutingData, issue #137).
"""
import asyncio
import json
import socket

import pytest

from bclib import edge
from bclib.context import RESTfulContext
from bclib.listener import Message
from bclib.listener.message_type import MessageType
from bclib.listener.tcp.tcp_message import TcpMessage


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def tcp_app():
    port = _free_port()
    app = edge.from_options(
        {"name": "pytest-tcp", "router": "restful", "tcp": f"127.0.0.1:{port}"})

    @app.restful_handler()
    async def hello(context: RESTfulContext):
        return {"hello": "world"}

    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    loop.run_until_complete(app.initialize_task_async())
    yield app, loop, port
    pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


async def _request_async(port: int, cms: dict) -> dict:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        await TcpMessage._write_to_stream_async(
            writer, "test-session", MessageType.AD_HOC, json.dumps(cms).encode("utf-8"))
        reply = await asyncio.wait_for(TcpMessage.read_from_stream_async(reader, writer), 5)
        return reply.cms_object if reply else None
    finally:
        writer.close()


def test_valid_request_is_answered_by_the_handler(tcp_app):
    _, loop, port = tcp_app
    cms = {"cms": {"request": {"full-url": "localhost/hello", "url": "hello", "methode": "get"}}}

    reply = loop.run_until_complete(_request_async(port, cms))

    assert json.loads(reply["cms"]["content"]) == {"hello": "world"}


def test_malformed_request_gets_an_error_reply_instead_of_a_closed_connection(tcp_app):
    _, loop, port = tcp_app

    reply = loop.run_until_complete(_request_async(port, {"cms": {"query": {}}}))

    assert reply is not None
    assert reply["cms"]["webserver"]["headercode"].startswith("500")
    assert "request key not found" in reply["cms"]["content"]


class _NoReplyMessage(Message):
    pass


def test_message_that_cannot_reply_still_raises(tcp_app):
    app, loop, _ = tcp_app
    with pytest.raises(Exception):
        loop.run_until_complete(app.on_message_receive_async(_NoReplyMessage()))
