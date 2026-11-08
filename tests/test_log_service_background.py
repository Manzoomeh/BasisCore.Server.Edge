"""log_in_background from sync handlers (worker threads) and RabbitMQ connection reuse."""
import asyncio
import threading

import pika
import pika.exceptions
import pytest

from bclib.log_service.log_object import LogObject
from bclib.log_service.log_schema import LogSchema
from bclib.log_service.log_service import LogService
from bclib.log_service.rabbit_schema_base_logger import RabbitSchemaBaseLogger
from bclib.log_service.schema_base_logger import SchemaBaseLogger

SCHEMA = {
    "schemaName": "test",
    "schemaVersion": "1.0.0",
    "lid": 1,
    "schemaId": "HASH",
    "paramUrl": "/freeform/x/HASH/fa/log",
    "questions": [{"title": "userId", "prpId": 1, "multi": False, "parts": [{"part": 1}]}],
}


class RecordingLogger(SchemaBaseLogger):
    """Schema logger that records saved schemas instead of sending them."""

    def __init__(self, loop=None):
        super().__init__({"url": "http://schema.invalid"}, loop=loop)
        self.saved = []
        self.saved_event = threading.Event()

    async def _SchemaBaseLogger__load_schema_async(self, schema_name):
        return LogSchema(SCHEMA)

    async def _save_schema_async(self, schema, routing_key=None):
        self.saved.append((schema, routing_key))
        self.saved_event.set()


def run_loop_in_thread():
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    return loop, thread


def stop_loop(loop, thread):
    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=5)
    loop.close()


def call_in_worker(fn):
    """Run fn in a plain worker thread, like Edge runs a sync handler."""
    result = {}

    def target():
        try:
            result["value"] = fn()
        except BaseException as ex:  # pragma: no cover - surfaced below
            result["error"] = ex

    worker = threading.Thread(target=target)
    worker.start()
    worker.join(timeout=5)
    if "error" in result:
        raise result["error"]
    return result.get("value")


def test_log_service_log_in_background_from_worker_thread_is_delivered():
    loop, thread = run_loop_in_thread()
    try:
        service = LogService({}, loop)
        recorder = RecordingLogger(loop)
        service._LogService__logger = recorder

        call_in_worker(lambda: service.log_in_background(
            service.new_object_log("freeform/x/HASH/fa/log", routing_key="temp", userId=7)))

        assert recorder.saved_event.wait(timeout=5), "log scheduled from a worker thread was never sent"
        schema, routing_key = recorder.saved[0]
        assert routing_key == "temp"
        assert schema["properties"][0]["answers"][0]["parts"][0]["values"][0]["value"] == 7
    finally:
        stop_loop(loop, thread)


def test_schema_logger_log_in_background_from_worker_thread_is_delivered():
    loop, thread = run_loop_in_thread()
    try:
        recorder = RecordingLogger(loop)

        call_in_worker(lambda: recorder.log_in_background(
            LogObject("freeform/x/HASH/fa/log", "temp", userId=7)))

        assert recorder.saved_event.wait(timeout=5), "log scheduled from a worker thread was never sent"
    finally:
        stop_loop(loop, thread)


def test_log_in_background_inside_loop_returns_task():
    async def scenario():
        recorder = RecordingLogger(asyncio.get_running_loop())
        service = LogService({}, asyncio.get_running_loop())
        service._LogService__logger = recorder
        task = service.log_in_background(LogObject("s", "temp", userId=1))
        assert isinstance(task, asyncio.Task)
        await task
        assert len(recorder.saved) == 1

    asyncio.run(scenario())


def test_log_in_background_without_logger_from_worker_thread_does_not_raise():
    loop, thread = run_loop_in_thread()
    try:
        service = LogService({}, loop)
        future = call_in_worker(lambda: service.log_in_background(LogObject("s", userId=1)))
        assert future.result(timeout=5) is None
    finally:
        stop_loop(loop, thread)


def test_schema_logger_without_any_loop_still_sends():
    recorder = RecordingLogger()
    call_in_worker(lambda: recorder.log_in_background(LogObject("s", "temp", userId=1)))
    assert len(recorder.saved) == 1


class FakeChannel:
    def __init__(self, connection):
        self.connection = connection

    def queue_declare(self, **kwargs):
        self.connection.declared += 1

    def basic_publish(self, **kwargs):
        if self.connection.fail_next_publish:
            self.connection.fail_next_publish = False
            self.connection.is_open = False
            raise pika.exceptions.StreamLostError("lost")
        self.connection.published.append(kwargs)


class FakeConnection:
    instances = []

    def __init__(self, params):
        self.is_open = True
        self.published = []
        self.declared = 0
        self.fail_next_publish = False
        self.closed = False
        FakeConnection.instances.append(self)

    def channel(self):
        return FakeChannel(self)

    def process_data_events(self, time_limit=None):
        if not self.is_open:
            raise pika.exceptions.ConnectionClosed(320, "closed")

    def close(self):
        self.is_open = False
        self.closed = True


@pytest.fixture
def fake_pika(monkeypatch):
    FakeConnection.instances = []
    monkeypatch.setattr(pika, "BlockingConnection", FakeConnection)
    return FakeConnection


def rabbit_logger(connection):
    return RabbitSchemaBaseLogger({"url": "http://schema.invalid", "connection": connection})


def test_rabbit_logger_reuses_one_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "LogDispatcherExchange"})

    async def scenario():
        for _ in range(5):
            await logger._save_schema_async({"a": 1}, "temp")

    asyncio.run(scenario())
    assert len(fake_pika.instances) == 1
    assert len(fake_pika.instances[0].published) == 5
    assert fake_pika.instances[0].published[0]["routing_key"] == "temp"
    assert fake_pika.instances[0].published[0]["exchange"] == "LogDispatcherExchange"


def test_rabbit_logger_declares_queue_once_per_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "queue": "logs", "durable": True})

    async def scenario():
        for _ in range(3):
            await logger._save_schema_async({"a": 1})

    asyncio.run(scenario())
    assert fake_pika.instances[0].declared == 1
    assert fake_pika.instances[0].published[0]["routing_key"] == "logs"


def test_rabbit_logger_reconnects_after_lost_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})

    async def scenario():
        await logger._save_schema_async({"n": 1}, "temp")
        fake_pika.instances[0].fail_next_publish = True
        await logger._save_schema_async({"n": 2}, "temp")

    asyncio.run(scenario())
    assert len(fake_pika.instances) == 2
    assert len(fake_pika.instances[0].published) == 1
    assert len(fake_pika.instances[1].published) == 1


def test_rabbit_logger_reconnects_when_server_closed_idle_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})

    async def scenario():
        await logger._save_schema_async({"n": 1}, "temp")
        fake_pika.instances[0].is_open = False  # e.g. missed heartbeats while idle
        await logger._save_schema_async({"n": 2}, "temp")

    asyncio.run(scenario())
    assert len(fake_pika.instances) == 2
    assert len(fake_pika.instances[1].published) == 1


def test_rabbit_logger_concurrent_publishes_share_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})

    async def scenario():
        await asyncio.gather(*(logger._save_schema_async({"n": i}, "temp") for i in range(20)))

    asyncio.run(scenario())
    assert len(fake_pika.instances) == 1
    assert len(fake_pika.instances[0].published) == 20


def test_rabbit_logger_close(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})
    asyncio.run(logger._save_schema_async({"n": 1}, "temp"))
    logger.close()
    assert fake_pika.instances[0].closed
