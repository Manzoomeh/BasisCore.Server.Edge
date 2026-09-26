"""
BasisEdge Playground — one process, all sample patterns + HTML console.

Run from repo root:
  set PYTHONPATH=.
  python examples/playground/app.py

Open: http://127.0.0.1:9300/
"""
from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from bclib import edge
from bclib.context import HttpContext, RESTfulContext, WebSocketContext
from bclib.exception import (
    BadRequestErr,
    ForbiddenErr,
    InternalServerErr,
    NotFoundErr,
    UnauthorizedErr,
)
from bclib.logger import ILogger
from bclib.utility import StaticFileHandler

ROOT = Path(__file__).resolve().parent
WWW = ROOT / "wwwroot"

options = {
    "name": "playground",
    "http": "127.0.0.1:9300",
    "router": {
        "restful": ["api/*"],
        "web": ["*"],
    },
    "cache": {"type": "memory", "clean_interval": 60, "reset_interval": 300},
    "logger": {"level": "INFO"},
    "log_request": True,
    "log_error": True,
}

app = edge.from_options(options)

# ---------------------------------------------------------------------------
# DI demo services
# ---------------------------------------------------------------------------


class IGreeter(ABC):
    @abstractmethod
    def greet(self, name: str) -> str: ...


class Greeter(IGreeter):
    def greet(self, name: str) -> str:
        return f"Hello, {name}! ({datetime.now():%H:%M:%S})"


class IClock(ABC):
    @abstractmethod
    def now(self) -> str: ...


class Clock(IClock):
    def now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")


app.service_provider.add_singleton(IGreeter, Greeter)
app.service_provider.add_singleton(IClock, Clock)

app.cache_manager.add_or_update(
    "demo",
    {"data": "static-data", "seeded_at": datetime.now().strftime("%H:%M:%S")},
    life_time=600,
)

app.add_static_handler(
    StaticFileHandler(
        base_dir=WWW,
        allowed_extensions={".html", ".css", ".js", ".svg", ".png", ".ico"},
        enable_index=True,
        index_files=["index.html"],
    )
)


# ---------------------------------------------------------------------------
# Catalog (also served as JSON for the HTML UI)
# ---------------------------------------------------------------------------

CATALOG = [
    {
        "group": "REST",
        "id": "hello",
        "title": "Hello REST",
        "desc": "Minimal JSON API — like examples/restful/hello.py",
        "method": "GET",
        "path": "/api/hello",
        "sample": "examples/restful/hello.py",
    },
    {
        "group": "REST",
        "id": "echo",
        "title": "URL segment",
        "desc": "Path param :name — like auto_router / simple REST routes",
        "method": "GET",
        "path": "/api/echo/Ada",
        "sample": "examples/di/auto_router.py",
    },
    {
        "group": "REST",
        "id": "items",
        "title": "Cached list",
        "desc": "@app.cache() on a data generator — like restful/simple.py",
        "method": "GET",
        "path": "/api/items",
        "sample": "examples/restful/simple.py",
    },
    {
        "group": "REST",
        "id": "item",
        "title": "Filter by id",
        "desc": "Route :id with cache-backed data",
        "method": "GET",
        "path": "/api/items/3",
        "sample": "examples/restful/simple.py",
    },
    {
        "group": "REST",
        "id": "large",
        "title": "Empty body → 400",
        "desc": "BadRequestErr when body missing — like restful/large_body.py",
        "method": "POST",
        "path": "/api/body",
        "body": None,
        "sample": "examples/restful/large_body.py",
    },
    {
        "group": "DI",
        "id": "greet",
        "title": "Inject IGreeter",
        "desc": "Singleton DI into handler — like di/simple_di.py",
        "method": "GET",
        "path": "/api/di/greet/Ada",
        "sample": "examples/di/simple_di.py",
    },
    {
        "group": "DI",
        "id": "no-ctx",
        "title": "Handler without context",
        "desc": "Only DI params — like di/optional_context.py",
        "method": "GET",
        "path": "/api/di/now",
        "sample": "examples/di/optional_context.py",
    },
    {
        "group": "Cache",
        "id": "cache-get",
        "title": "Cache manager get",
        "desc": "cache_manager.get_cache — like cache/simple.py",
        "method": "GET",
        "path": "/api/cache/demo",
        "sample": "examples/cache/simple.py",
    },
    {
        "group": "Cache",
        "id": "cache-method",
        "title": "@app.cache on handler",
        "desc": "Decorator cache (call twice; second is faster) — cache/cache_method.py",
        "method": "GET",
        "path": "/api/cache/slow",
        "sample": "examples/cache/cache_method.py",
    },
    {
        "group": "Exceptions",
        "id": "ex-400",
        "title": "BadRequest 400",
        "desc": "raise BadRequestErr — exceptions/bad_request.py",
        "method": "GET",
        "path": "/api/errors/bad-request",
        "sample": "examples/exceptions/bad_request.py",
        "expectError": True,
    },
    {
        "group": "Exceptions",
        "id": "ex-401",
        "title": "Unauthorized 401",
        "desc": "raise UnauthorizedErr — exceptions/rest_unauthorized.py",
        "method": "GET",
        "path": "/api/errors/unauthorized",
        "sample": "examples/exceptions/rest_unauthorized.py",
        "expectError": True,
    },
    {
        "group": "Exceptions",
        "id": "ex-403",
        "title": "Forbidden 403",
        "desc": "raise ForbiddenErr — exceptions/forbidden.py",
        "method": "GET",
        "path": "/api/errors/forbidden",
        "sample": "examples/exceptions/forbidden.py",
        "expectError": True,
    },
    {
        "group": "Exceptions",
        "id": "ex-404",
        "title": "NotFound 404",
        "desc": "raise NotFoundErr — exceptions/not_found.py",
        "method": "GET",
        "path": "/api/errors/not-found",
        "sample": "examples/exceptions/not_found.py",
        "expectError": True,
    },
    {
        "group": "Exceptions",
        "id": "ex-500",
        "title": "InternalServer 500",
        "desc": "raise InternalServerErr with payload — exceptions/custom_content.py",
        "method": "GET",
        "path": "/api/errors/internal",
        "sample": "examples/exceptions/custom_content.py",
        "expectError": True,
    },
    {
        "group": "Predicates",
        "id": "admin-ok",
        "title": "Callback + query token",
        "desc": "has_value / callback style gate — predicates/",
        "method": "GET",
        "path": "/api/admin/stats?token=secret",
        "sample": "examples/predicates/callback.py",
    },
    {
        "group": "Predicates",
        "id": "admin-deny",
        "title": "Missing token → no match / error",
        "desc": "Same route without token",
        "method": "GET",
        "path": "/api/admin/stats",
        "sample": "examples/predicates/decorator_parameters.py",
        "expectError": True,
    },
    {
        "group": "Logger",
        "id": "log",
        "title": "ILogger injection",
        "desc": "Watch console for log lines — logger/di_logger.py",
        "method": "GET",
        "path": "/api/logger/ping",
        "sample": "examples/logger/di_logger.py",
    },
    {
        "group": "Streaming",
        "id": "stream",
        "title": "Chunked REST stream",
        "desc": "start_stream_response_async — streaming/rest_stream.py",
        "method": "GET",
        "path": "/api/stream",
        "sample": "examples/streaming/rest_stream.py",
        "stream": True,
    },
    {
        "group": "Web",
        "id": "web-hello",
        "title": "HTML web handler",
        "desc": "web_handler returning HTML — web/simple.py",
        "method": "GET",
        "path": "/web/hello",
        "sample": "examples/web/simple.py",
        "html": True,
    },
    {
        "group": "WebSocket",
        "id": "ws",
        "title": "WebSocket echo",
        "desc": "Connect from this page — websocket/simple.py",
        "method": "WS",
        "path": "/ws/echo",
        "sample": "examples/websocket/simple.py",
        "websocket": True,
    },
]


@app.restful_handler("api/catalog", method="GET")
def catalog():
    return {"port": 9300, "endpoints": CATALOG}


# ---------------------------------------------------------------------------
# REST handlers
# ---------------------------------------------------------------------------


@app.restful_handler("api/hello", method="GET")
def hello(context: RESTfulContext):
    return {"message": "Hello BasisEdge", "url": context.url}


@app.restful_handler("api/echo/:name", method="GET")
def echo(context: RESTfulContext):
    return {"hello": context.url_segments["name"]}


@app.cache()
def generate_items() -> list:
    import random
    import string

    return [
        {
            "id": i,
            "data": "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        }
        for i in range(10)
    ]


@app.restful_handler("api/items", method="GET")
def items_all(_: RESTfulContext):
    return generate_items()


@app.restful_handler("api/items/:id", method="GET")
def items_one(context: RESTfulContext):
    item_id = int(context.url_segments["id"])
    return [row for row in generate_items() if row["id"] == item_id]


@app.restful_handler("api/body", method="POST")
def body_len(context: RESTfulContext):
    body = context.body
    if body is None:
        raise BadRequestErr(message="empty body", data={"result": "incorrect inputs"})
    return {"bytes": len(json.dumps(body, ensure_ascii=False))}


@app.restful_handler("api/di/greet/:name", method="GET")
def di_greet(context: RESTfulContext, greeter: IGreeter):
    return {"text": greeter.greet(context.url_segments["name"])}


@app.restful_handler("api/di/now", method="GET")
def di_now(clock: IClock):
    return {"now": clock.now(), "note": "no context param"}


@app.restful_handler("api/cache/slow", method="GET")
@app.cache(30, "slow-demo")
def cache_slow(_: RESTfulContext):
    time.sleep(0.4)
    return {"data": "static-data", "time": datetime.now().strftime("%H:%M:%S")}


@app.restful_handler("api/cache/:key", method="GET")
def cache_get(context: RESTfulContext):
    key = context.url_segments["key"]
    return {"From Cache": context.dispatcher.cache_manager.get_cache(key)}


@app.restful_handler("api/errors/bad-request", method="GET")
def err_400(_: RESTfulContext):
    raise BadRequestErr(data={"error": "bad request"})


@app.restful_handler("api/errors/unauthorized", method="GET")
def err_401(_: RESTfulContext):
    raise UnauthorizedErr("missing token")


@app.restful_handler("api/errors/forbidden", method="GET")
def err_403(_: RESTfulContext):
    raise ForbiddenErr(data={"error": "forbidden"})


@app.restful_handler("api/errors/not-found", method="GET")
def err_404(_: RESTfulContext):
    raise NotFoundErr("item not found")


@app.restful_handler("api/errors/internal", method="GET")
def err_500(_: RESTfulContext):
    raise InternalServerErr(None, {"code": "12-33", "type": "custom", "msg": "error message"})


@app.restful_handler(
    "api/admin/stats",
    app.has_value("context.query.token"),
    method="GET",
)
def admin_stats(context: RESTfulContext):
    return {"ok": True, "token": context.query.get("token"), "area": "admin"}


@app.restful_handler("api/logger/ping", method="GET")
def logger_ping(logger: ILogger["Playground"]):
    logger.info("playground ping")
    return {"ok": True, "logged": True}


@app.restful_handler("api/stream", method="GET")
async def rest_stream(context: RESTfulContext):
    await context.start_stream_response_async(
        status=200,
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    for i in range(5):
        await context.write_async(f"Chunk {i + 1}\n".encode("utf-8"))
        await context.drain_async()
        await asyncio.sleep(0.15)
    return None


# ---------------------------------------------------------------------------
# Web + WebSocket
# ---------------------------------------------------------------------------


@app.web_handler("web/hello", method="GET")
def web_hello(_: HttpContext):
    return "<h1>Hello from web_handler</h1><p>Like examples/web/simple.py</p>"


@app.handler("ws/echo")
async def ws_echo(context: WebSocketContext):
    session = context.session
    if context.message.is_connect:
        await session.send_json_async(
            {"type": "welcome", "message": "WS connected", "session": session.id[:8]}
        )
    elif context.message.is_text:
        text = context.message.text
        try:
            data = json.loads(text)
            await session.send_json_async({"type": "echo", "original": data})
        except json.JSONDecodeError:
            await session.send_text_async(f"echo: {text}")


if __name__ == "__main__":
    print("Playground → http://127.0.0.1:9300/")
    print("Catalog JSON → http://127.0.0.1:9300/api/catalog")
    app.listening()
