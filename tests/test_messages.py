"""Message type constructors."""
from unittest.mock import MagicMock

from bclib.listener.http.http_message import HttpMessage
from bclib.listener.http.websocket_message import WSMessageType, WebSocketMessage
from bclib.listener.message_type import MessageType
from bclib.listener.rabbit.rabbit_message import RabbitMessage
from bclib.listener.tcp.tcp_message import TcpMessage

from helpers import make_cms, mock_ws_session


def test_http_message():
    cms = make_cms(url="x")
    msg = HttpMessage(cms)
    assert msg.cms_object == cms


def test_rabbit_message_text():
    msg = RabbitMessage("h", "q", b"hi")
    assert msg.message_text == "hi"


def test_tcp_message_construct():
    reader = MagicMock()
    writer = MagicMock()
    msg = TcpMessage(reader, writer, "sid-1", MessageType.MESSAGE, buffer=b"abc")
    assert msg.session_id == "sid-1"
    assert msg.type == MessageType.MESSAGE


def test_websocket_message_factories():
    session = mock_ws_session()
    connect = WebSocketMessage.connect(session, MessageType.CONNECT)
    text = WebSocketMessage.text_message(session, MessageType.MESSAGE, "ping")
    binary = WebSocketMessage.binary_message(session, MessageType.MESSAGE, b"\x01")
    close = WebSocketMessage.close_message(session, MessageType.DISCONNECT, 1000)

    assert connect.is_connect
    assert text.is_text and text.text == "ping"
    assert binary.is_binary and binary.binary == b"\x01"
    assert close.is_close
    assert text.ws_type == WSMessageType.TEXT
