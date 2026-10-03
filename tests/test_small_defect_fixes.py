"""Regression tests for small defects: Mongo close, static prefix/dotfiles, 404 logging."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from bclib.connections.mongo.mongo_connection import MongoConnection
from bclib.context import RESTfulContext
from bclib.utility.static_file_handler import StaticFileHandler

from helpers import http_context, make_cms, run_dispatch


# --- MongoConnection close -------------------------------------------------

def _mongo_with_mock_clients():
    connection = MongoConnection(
        {"connection_string": "mongodb://x:27017", "database_name": "db"})
    sync_client = MagicMock()
    async_client = MagicMock()
    async_client.close = AsyncMock()
    connection._client = sync_client
    connection._database = MagicMock()
    connection._async_client = async_client
    connection._async_database = MagicMock()
    return connection, sync_client, async_client


def test_mongo_close_async_awaits_async_client():
    connection, sync_client, async_client = _mongo_with_mock_clients()

    asyncio.run(connection.close_async())

    sync_client.close.assert_called_once()
    async_client.close.assert_awaited_once()
    assert connection._client is None and connection._async_client is None
    assert connection._database is None and connection._async_database is None


def test_mongo_sync_close_does_not_leak_unawaited_coroutine():
    connection, sync_client, async_client = _mongo_with_mock_clients()

    connection.close()

    sync_client.close.assert_called_once()
    # Awaited (not merely called): no coroutine is left un-awaited.
    async_client.close.assert_awaited_once()
    assert connection._async_client is None


def test_mongo_sync_close_inside_running_loop_schedules_async_close():
    connection, _, async_client = _mongo_with_mock_clients()

    async def scenario():
        connection.close()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    asyncio.run(scenario())
    async_client.close.assert_awaited_once()


# --- StaticFileHandler -----------------------------------------------------

def _static_context(url: str):
    context = MagicMock()
    context.cms = {"request": {"url": url}}
    return context


@pytest.mark.parametrize("prefix", ["/static", "static", "/static/", "static/"])
def test_static_prefix_matches_url_without_leading_slash(tmp_path: Path, prefix):
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    handler = StaticFileHandler(str(tmp_path), url_prefix=prefix)

    # Request URLs reach handlers without a leading slash (path[1:]).
    body = asyncio.run(handler.handle(_static_context("static/app.js")))
    assert body == b"console.log(1)"
    assert handler._normalize_url_path("/static/app.js") == "app.js"
    # A different segment that merely starts with the prefix is not stripped.
    assert handler._normalize_url_path("staticfoo/app.js") == "staticfoo/app.js"


def test_static_hidden_files_not_served_by_default(tmp_path: Path):
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]", encoding="utf-8")
    (tmp_path / "ok.txt").write_text("ok", encoding="utf-8")
    handler = StaticFileHandler(str(tmp_path))

    assert asyncio.run(handler.handle(_static_context(".env"))) is None
    assert asyncio.run(handler.handle(_static_context(".git/config"))) is None
    assert asyncio.run(handler.handle(_static_context("ok.txt"))) == b"ok"


def test_static_hidden_files_served_when_allowed(tmp_path: Path):
    (tmp_path / ".well-known").mkdir()
    (tmp_path / ".well-known" / "security.txt").write_text("c", encoding="utf-8")
    handler = StaticFileHandler(str(tmp_path), allow_hidden=True)

    body = asyncio.run(handler.handle(_static_context(".well-known/security.txt")))
    assert body == b"c"


# --- dispatch_async logging ------------------------------------------------

def _swap_logger(app):
    logger = MagicMock()
    app._Dispatcher__logger = logger
    return logger


def test_handler_not_found_logged_as_warning_without_traceback(app):
    logger = _swap_logger(app)

    cms = make_cms(url="wp-login.php", method="get")
    run_dispatch(app, http_context(app, cms, RESTfulContext))

    logger.error.assert_not_called()
    logger.warning.assert_called_once()
    assert not logger.warning.call_args.kwargs.get("exc_info")


def test_real_exception_still_logged_as_error_with_traceback(app):
    @app.restful_handler("boom", method="GET")
    def boom(context: RESTfulContext):
        raise RuntimeError("boom")

    logger = _swap_logger(app)
    cms = make_cms(url="boom", method="get")
    run_dispatch(app, http_context(app, cms, RESTfulContext))

    logger.error.assert_called_once()
    assert logger.error.call_args.kwargs.get("exc_info") is True
