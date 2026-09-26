"""Shared helpers for the Edge unit suite (importable from test modules)."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from bclib.dispatcher import IDispatcher
from bclib.listener.http.http_message import HttpMessage
from bclib.listener.http.websocket_message import WebSocketMessage
from bclib.listener.message_type import MessageType


def make_cms(
    url: str = "hello",
    method: str = "get",
    body: str = "{}",
    content_type: str = "application/json",
    query: dict | None = None,
    form: dict | None = None,
) -> dict[str, Any]:
    return {
        "request": {
            "url": url,
            "methode": method,
            "content-type": content_type,
            "body": body,
        },
        "query": query or {},
        "form": form or {},
    }


def http_context(app: IDispatcher, cms: dict, context_cls):
    return context_cls(cms, app, HttpMessage(cms))


def run_dispatch(app: IDispatcher, context) -> Any:
    """Run dispatch_async on the dispatcher event loop (avoids loop mismatch)."""
    import asyncio

    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    return loop.run_until_complete(app.dispatch_async(context))


def cms_content(result: dict) -> Any:
    """Extract handler payload from CMS-wrapped response."""
    import json

    content = result.get("cms", {}).get("content")
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    return content


def mock_ws_session(cms: dict | None = None) -> MagicMock:
    session = MagicMock()
    session.id = "sess-test-12345678"
    session.cms_object = cms or make_cms(url="ws/chat")
    session.session_manager = MagicMock()
    return session


def ws_text_message(cms: dict | None = None) -> WebSocketMessage:
    return WebSocketMessage.text_message(
        mock_ws_session(cms), MessageType.MESSAGE, "hello"
    )
