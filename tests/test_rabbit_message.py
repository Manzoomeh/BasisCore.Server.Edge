"""Unit tests for RabbitMessage without requiring pika types."""
from types import SimpleNamespace

from bclib.listener.rabbit.rabbit_message import RabbitMessage


def test_rabbit_message_basic_fields():
    message = RabbitMessage(
        host="localhost",
        queue="tasks",
        body=b'{"ok": true}',
        routing_key="task.process",
    )

    assert message.host == "localhost"
    assert message.queue == "tasks"
    assert message.routing_key == "task.process"
    assert message.message_text == '{"ok": true}'
    assert message.delivery_tag is None
    assert message.exchange is None
    assert message.content_type is None
    assert message.headers == {}


def test_rabbit_message_extracts_method_and_properties():
    method = SimpleNamespace(delivery_tag=42, exchange="events")
    properties = SimpleNamespace(
        content_type="application/json",
        headers={"x-trace": "abc"},
    )

    message = RabbitMessage(
        host="mq",
        queue="q",
        body=b"payload",
        method=method,
        properties=properties,
    )

    assert message.delivery_tag == 42
    assert message.exchange == "events"
    assert message.content_type == "application/json"
    assert message.headers == {"x-trace": "abc"}
