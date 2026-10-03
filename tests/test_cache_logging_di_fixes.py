"""Regression tests: custom ILogger precedence, @app.cache keying, rabbit signaler
start-up, ILogService with an untyped logger section, constructor error reporting."""
import asyncio
import time
from typing import Type, TypeVar
from unittest.mock import MagicMock, patch

import pytest

from bclib import edge
from bclib.cache.in_memory_cache_manager import InMemoryCacheManager
from bclib.context import RESTfulContext
from bclib.di import ServiceProvider
from bclib.log_service import ILogService
from bclib.logger import ILogger
from bclib.logger.console_logger import ConsoleLogger
from bclib.options.app_options import AppOptions
from bclib.utility import DictEx

from helpers import cms_content, http_context, make_cms, run_dispatch

T = TypeVar("T")


class RecordingLogger(ILogger[T]):
    def __init__(self, options: AppOptions, generic_type_args: tuple[Type, ...] = None):
        super().__init__("RecordingLogger")


def _logger_class_seen_by_handler(app) -> str:
    @app.restful_handler("api/which-logger", method="GET")
    def which_logger(context: RESTfulContext, logger: ILogger[None]):
        return {"logger": type(logger).__name__}

    cms = make_cms(url="api/which-logger", method="get")
    return cms_content(run_dispatch(app, http_context(app, cms, RESTfulContext)))["logger"]


# --- 1. custom ILogger registered after from_options -------------------------

def test_custom_logger_registered_after_from_options_is_injected():
    default_app = edge.from_options({"name": "default-logger", "router": "restful"})
    assert _logger_class_seen_by_handler(default_app) == "ConsoleLogger"

    app = edge.from_options({"name": "custom-logger", "router": "restful"})
    app.service_provider.add_singleton(ILogger, RecordingLogger)
    assert _logger_class_seen_by_handler(app) == "RecordingLogger"
    assert isinstance(app.service_provider.get_service(ILogger["X"]), RecordingLogger)
    assert [type(x) for x in app.service_provider.get_service(list[ILogger])] == [RecordingLogger]


def test_default_registration_never_displaces_an_explicit_one():
    services = ServiceProvider()
    services.add_singleton(ILogger, RecordingLogger)
    services.add_singleton(ILogger, ConsoleLogger, is_default=True)
    services.add_singleton(AppOptions, instance={})
    assert isinstance(services.get_service(ILogger["X"]), RecordingLogger)

    # explicit registrations keep first-wins and list[T] keeps all of them
    class IThing: ...
    class A(IThing): ...
    class B(IThing): ...

    services.add_singleton(IThing, A)
    services.add_singleton(IThing, B)
    assert isinstance(services.get_service(IThing), A)
    assert [type(x) for x in services.get_service(list[IThing])] == [A, B]


# --- 2. @app.cache keyed by arguments, async support -------------------------

def _memory_cache() -> InMemoryCacheManager:
    return InMemoryCacheManager(DictEx({"type": "memory", "clean_interval": 0, "reset_interval": 0}))


def test_cache_is_keyed_by_arguments():
    calls = []

    @_memory_cache().cache_decorator()
    def square(x, scale=1):
        calls.append(x)
        return x * x * scale

    assert square(2) == 4
    assert square(3) == 9
    assert square(2) == 4
    assert square(2, scale=10) == 40
    assert calls == [2, 3, 2]


def test_cache_no_arg_function_and_key_lookup_alongside_argument_keyed_one():
    calls = []
    manager = _memory_cache()

    @manager.cache_decorator(key="numbers")
    def numbers():
        calls.append("numbers")
        return [1, 2, 3]

    @manager.cache_decorator()
    def label(x):
        calls.append(x)
        return f"label-{x}"

    assert numbers() == [1, 2, 3]
    assert numbers() == [1, 2, 3]
    assert manager.get_cache("numbers") == [[1, 2, 3]]
    assert label("a") == "label-a"
    assert label("b") == "label-b"
    assert calls == ["numbers", "a", "b"]


def test_cache_supports_unhashable_arguments():
    calls = []

    @_memory_cache().cache_decorator()
    def total(values):
        calls.append(1)
        return sum(values)

    assert total([1, 2]) == 3
    assert total([1, 2]) == 3
    assert total([2, 2]) == 4
    assert len(calls) == 2


def test_cache_supports_async_functions():
    calls = []

    @_memory_cache().cache_decorator()
    async def fetch(x):
        calls.append(x)
        return x + 1

    async def run():
        return [await fetch(1), await fetch(1), await fetch(2)]

    assert asyncio.run(run()) == [2, 2, 3]
    assert calls == [1, 2]


def test_cache_life_time_expires_entries():
    calls = []

    @_memory_cache().cache_decorator(life_time=1)
    def stamp(x):
        calls.append(x)
        return len(calls)

    assert stamp("a") == 1
    assert stamp("a") == 1
    assert stamp("b") == 2
    with patch("bclib.cache.cache_item.base_cache_item.time.time", return_value=time.time() + 5):
        assert stamp("a") == 3
    assert stamp("b") == 2
    assert calls == ["a", "b", "a"]


# --- 3. rabbit cache signaler does not need a running loop at construction ----

def test_from_options_with_rabbit_signaler_does_not_connect():
    with patch("pika.BlockingConnection") as connection:
        app = edge.from_options({
            "name": "rabbit-signaler",
            "router": "restful",
            "cache": {
                "type": "memory", "clean_interval": 0, "reset_interval": 0,
                "signaler": {"type": "rabbit", "url": "amqp://guest:guest@localhost:5672/", "queue": "cache"},
            },
        })
        assert isinstance(app.cache_manager, InMemoryCacheManager)
        connection.assert_not_called()


def test_rabbit_signaler_connects_when_started_on_the_loop():
    from bclib.cache.signaler.rabbit_signaler import RabbitSignaller

    signaler = RabbitSignaller(lambda keys: None, DictEx(
        {"type": "rabbit", "url": "amqp://guest:guest@localhost:5672/", "queue": "cache"}))
    with patch("pika.BlockingConnection") as connection:
        channel = MagicMock()
        connection.return_value.channel.return_value = channel

        async def run():
            signaler.start()
            await asyncio.sleep(0)

        asyncio.run(run())
        connection.assert_called_once()
        channel.queue_declare.assert_called_once_with(queue="cache")
        channel.basic_consume.assert_called_once()


# --- 4. ILogService with a logger section that has no type --------------------

def test_log_service_with_untyped_logger_section_is_no_op():
    app = edge.from_options({"name": "log-svc", "router": "restful", "logger": {"level": "INFO"}})
    log_service = app.service_provider.get_service(ILogService)
    assert log_service is not None
    log_object = log_service.new_object_log("schema", user=1)
    assert log_object is not None


# --- 5. constructor exceptions are not hidden ---------------------------------

def test_constructor_error_is_not_hidden_by_parameterless_retry():
    class Dependency: ...

    class Broken:
        def __init__(self, dependency: Dependency):
            raise ValueError("boom from constructor")

    services = ServiceProvider()
    services.add_singleton(Dependency)
    services.add_singleton(Broken)
    with pytest.raises(ValueError, match="boom from constructor"):
        services.get_service(Broken)
