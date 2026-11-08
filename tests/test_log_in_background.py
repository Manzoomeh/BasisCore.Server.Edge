"""dispatcher.log_in_background from sync handlers (worker threads) and RabbitMQ connection reuse."""
import asyncio
import threading

import pika
import pika.exceptions
import pytest

from bclib.dispatcher.dispatcher import Dispatcher
from bclib.logger.log_object import LogObject
from bclib.logger.rabbit_schema_base_logger import RabbitSchemaBaseLogger
from bclib.utility import DictEx


class TestDispatcher(Dispatcher):
    """Concrete dispatcher for tests; listening is not needed."""
    __test__ = False

    def initialize_task(self):  # pragma: no cover - not used
        pass


class RecordingLogger:
    def __init__(self):
        self.saved = []
        self.saved_event = threading.Event()

    def new_object_log(self, schema_name, routing_key=None, **kwargs):
        return LogObject(schema_name, routing_key, **kwargs)

    async def log_async(self, log_object):
        self.saved.append(log_object)
        self.saved_event.set()


def make_dispatcher(loop):
    dispatcher = TestDispatcher({}, loop)
    recorder = RecordingLogger()
    dispatcher._Dispatcher__logger = recorder
    return dispatcher, recorder


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


def test_log_in_background_from_worker_thread_is_delivered():
    loop, thread = run_loop_in_thread()
    try:
        dispatcher, recorder = make_dispatcher(loop)
        call_in_worker(lambda: dispatcher.log_in_background(
            dispatcher.new_object_log("freeform/x/HASH/fa/log", routing_key="temp", userId=7)))
        assert recorder.saved_event.wait(timeout=5), "log scheduled from a worker thread was never sent"
        assert recorder.saved[0].routingKey == "temp"
        assert recorder.saved[0].properties == {"userId": [[7]]}
    finally:
        stop_loop(loop, thread)


def test_log_in_background_with_kwargs_from_worker_thread_is_delivered():
    loop, thread = run_loop_in_thread()
    try:
        dispatcher, recorder = make_dispatcher(loop)
        call_in_worker(lambda: dispatcher.log_in_background(schema_name="s", userId=1))
        assert recorder.saved_event.wait(timeout=5)
    finally:
        stop_loop(loop, thread)


def test_log_in_background_inside_loop_returns_task():
    async def scenario():
        dispatcher, recorder = make_dispatcher(asyncio.get_running_loop())
        task = dispatcher.log_in_background(LogObject("s", "temp", userId=1))
        assert isinstance(task, asyncio.Task)
        await task
        assert len(recorder.saved) == 1

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(scenario())
    finally:
        loop.close()


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
    return RabbitSchemaBaseLogger(DictEx({"url": "http://schema.invalid", "connection": connection}))


def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_rabbit_logger_reuses_one_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "LogDispatcherExchange"})

    async def scenario():
        for _ in range(5):
            await logger._save_schema_async({"a": 1}, "temp")

    run(scenario())
    assert len(fake_pika.instances) == 1
    assert len(fake_pika.instances[0].published) == 5
    assert fake_pika.instances[0].published[0]["routing_key"] == "temp"
    assert fake_pika.instances[0].published[0]["exchange"] == "LogDispatcherExchange"


def test_rabbit_logger_declares_queue_once_per_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "queue": "logs", "durable": True})

    async def scenario():
        for _ in range(3):
            await logger._save_schema_async({"a": 1})

    run(scenario())
    assert fake_pika.instances[0].declared == 1
    assert fake_pika.instances[0].published[0]["routing_key"] == "logs"


def test_rabbit_logger_reconnects_after_lost_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})

    async def scenario():
        await logger._save_schema_async({"n": 1}, "temp")
        fake_pika.instances[0].fail_next_publish = True
        await logger._save_schema_async({"n": 2}, "temp")

    run(scenario())
    assert len(fake_pika.instances) == 2
    assert len(fake_pika.instances[0].published) == 1
    assert len(fake_pika.instances[1].published) == 1


def test_rabbit_logger_reconnects_when_server_closed_idle_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})

    async def scenario():
        await logger._save_schema_async({"n": 1}, "temp")
        fake_pika.instances[0].is_open = False  # e.g. missed heartbeats while idle
        await logger._save_schema_async({"n": 2}, "temp")

    run(scenario())
    assert len(fake_pika.instances) == 2
    assert len(fake_pika.instances[1].published) == 1


def test_rabbit_logger_concurrent_publishes_share_connection(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})

    async def scenario():
        await asyncio.gather(*(logger._save_schema_async({"n": i}, "temp") for i in range(20)))

    run(scenario())
    assert len(fake_pika.instances) == 1
    assert len(fake_pika.instances[0].published) == 20


def test_rabbit_logger_close(fake_pika):
    logger = rabbit_logger({"url": "amqp://x", "exchange": "ex"})
    run(logger._save_schema_async({"n": 1}, "temp"))
    logger.close()
    assert fake_pika.instances[0].closed
