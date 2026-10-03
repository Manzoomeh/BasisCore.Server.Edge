# Testing

This page covers testing an application built on BasisEdge and adding tests to the
BasisEdge repository. Both use pytest and the same technique: build the app with
`edge.from_options`, build a context, and run `dispatch_async` on the app's own event loop.
No port is opened and `app.listening()` is never called.

## Running the repository suite

```bash
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
pytest                                # the whole suite
pytest -v tests/test_handlers.py      # one module
pytest tests/test_handlers.py -k url_segments
```

`pytest.ini` at the repository root collects only `tests/test_*.py`, puts the checkout on
`sys.path` (so `bclib` imports from source even without an install), runs with
`-q --tb=short`, and hides `DeprecationWarning`. The suite needs no external services and
finishes in a few seconds.

The `tests` workflow in `.github/workflows/tests.yml` runs on every pull request and on
pushes to `master`, `main` and `qamsari/**`. It installs both requirement files and the
package on `ubuntu-latest` with Python 3.13, then runs `pytest`. Match that Python version
locally before opening a pull request.

## Fixtures and helpers

`tests/conftest.py` provides two function-scoped fixtures, so every test gets a new app:

| Fixture | What it builds |
|---------|----------------|
| `app` | A fresh app from `from_options` named `pytest-edge` |
| `connected_app` | Adds `database`, `rabbitmq` and `external_api` sections, for resolving connection services. Connections are created lazily, so no server is contacted unless a test uses one. |

`tests/helpers.py` is imported directly (`from helpers import ...`):

| Helper | Purpose |
|--------|---------|
| `make_cms(url, method, body, content_type, query, form)` | Builds the inner CMS dict a context reads (`request.url`, `request.methode`, `query`, `form`) |
| `http_context(app, cms, context_cls)` | Instantiates `context_cls(cms, app, HttpMessage(cms))` |
| `run_dispatch(app, context)` | Runs `app.dispatch_async(context)` on the app's loop and returns the CMS response |
| `cms_content(result)` | Returns `result["cms"]["content"]`, JSON-decoded when possible |
| `mock_ws_session(cms)`, `ws_text_message(cms)` | A mocked WebSocket session and a text message for `WebSocketContext` tests |

A test contributed to the repository looks like this:

```python
from bclib.context import RESTfulContext

from helpers import cms_content, http_context, make_cms, run_dispatch


def test_query_value_reaches_handler(app):
    @app.restful_handler("api/echo", method="GET")
    def echo(context: RESTfulContext):
        return {"q": context.query.get("q")}

    cms = make_cms(url="api/echo", method="get", query={"q": "x"})
    result = run_dispatch(app, http_context(app, cms, RESTfulContext))
    assert cms_content(result) == {"q": "x"}
```

Put it in `tests/test_<area>.py`, next to the module that covers the same area, and keep
tests independent of the network unless the transport itself is under test.

## Testing an application's handlers

An application gets the same isolation by building its app in a factory function, so each
test creates a fresh app and can pass in fakes. Because the first DI registration of a type
wins (see [extending.md](extending.md)), the factory chooses the implementation instead of a
test registering a second one afterwards.

`shop.py`:

```python
from abc import ABC, abstractmethod

from bclib import edge
from bclib.context import RESTfulContext
from bclib.dispatcher import IDispatcher
from bclib.exception import NotFoundErr


class IPriceStore(ABC):
    @abstractmethod
    def price(self, sku: str) -> float | None: ...


class DbPriceStore(IPriceStore):
    def price(self, sku: str) -> float | None:
        raise RuntimeError("needs a database")


def create_app(options: dict, price_store: type[IPriceStore] = DbPriceStore) -> IDispatcher:
    app = edge.from_options(options)
    app.service_provider.add_singleton(IPriceStore, price_store)

    @app.restful_handler("api/price/:sku", method="GET")
    def get_price(sku: str, store: IPriceStore):
        value = store.price(sku)
        if value is None:
            raise NotFoundErr(f"unknown sku {sku}")
        return {"sku": sku, "price": value}

    return app
```

`test_shop.py`:

```python
import asyncio
import json

import pytest

from bclib.context import RESTfulContext
from bclib.listener.http.http_message import HttpMessage

from shop import IPriceStore, create_app


class FakePriceStore(IPriceStore):
    def price(self, sku: str) -> float | None:
        return {"A-1": 9.5}.get(sku)


@pytest.fixture
def app():
    return create_app({"name": "shop-test", "logger": {"level": "WARNING"}},
                      price_store=FakePriceStore)


def dispatch(app, url: str, method: str = "get") -> dict:
    cms = {"request": {"url": url, "methode": method}, "query": {}, "form": {}}
    context = RESTfulContext(cms, app, HttpMessage(cms))
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    return loop.run_until_complete(app.dispatch_async(context))


def test_known_sku_returns_price(app):
    result = dispatch(app, "api/price/A-1")
    assert result["cms"]["webserver"]["headercode"] == "200 OK"
    assert json.loads(result["cms"]["content"]) == {"sku": "A-1", "price": 9.5}


def test_unknown_sku_is_404(app):
    result = dispatch(app, "api/price/Z-9")
    assert result["cms"]["webserver"]["headercode"].startswith("404")


def test_wrong_method_finds_no_handler(app):
    result = dispatch(app, "api/price/A-1", method="post")
    assert result["cms"]["webserver"]["headercode"].startswith("404")
    assert "Suitable handler not found" in json.loads(result["cms"]["content"])["errorMessage"]
```

```text
$ pytest -v test_shop.py
collecting ... collected 3 items

test_shop.py::test_known_sku_returns_price PASSED                        [ 33%]
test_shop.py::test_unknown_sku_is_404 PASSED                             [ 66%]
test_shop.py::test_wrong_method_finds_no_handler PASSED                  [100%]

============================== 3 passed in 1.14s ==============================
```

Points to keep in mind:

- `dispatch_async` never raises for handler errors. Exceptions, including "no handler
  found", come back as a CMS error response, so assert on `cms.webserver.headercode` and the
  JSON `errorMessage`. Status codes are listed in
  [Errors & Status Codes](../README.md#16-errors--status-codes).
- The CMS request uses the key `methode`, not `method`.
- A context built directly skips the URL router, so pick the context class the handler
  expects (`RESTfulContext` for `restful_handler`, `HttpContext` for `web_handler`, ...).
- Hosted services do not start. If a test depends on one, run
  `loop.run_until_complete(app.initialize_task_async())` first and
  `app.service_provider.stop_hosted_services_async()` at the end.

## Testing over a real TCP connection

To test the transport itself, configure a `tcp` listener on a free port and start it with
`initialize_task_async()`, which is what `listening()` runs before it blocks.
`tests/test_error_reply.py` is the reference; condensed:

```python
import asyncio
import json
import socket

import pytest

from bclib import edge
from bclib.context import RESTfulContext
from bclib.listener.message_type import MessageType
from bclib.listener.tcp.tcp_message import TcpMessage


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def tcp_app():
    port = _free_port()
    app = edge.from_options({"name": "pytest-tcp", "tcp": f"127.0.0.1:{port}"})

    @app.restful_handler("ping")
    async def ping(context: RESTfulContext):
        return {"pong": True}

    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    loop.run_until_complete(app.initialize_task_async())
    yield loop, port
    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


async def _request_async(port: int, cms: dict) -> dict:
    for _ in range(50):  # the listener binds in a background task
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            break
        except ConnectionRefusedError:
            await asyncio.sleep(0.1)
    try:
        await TcpMessage._write_to_stream_async(
            writer, "test-session", MessageType.AD_HOC, json.dumps(cms).encode("utf-8"))
        reply = await asyncio.wait_for(TcpMessage.read_from_stream_async(reader, writer), 5)
        return reply.cms_object
    finally:
        writer.close()


def test_ping_over_tcp(tcp_app):
    loop, port = tcp_app
    cms = {"cms": {"request": {"full-url": "localhost/ping", "url": "ping", "methode": "get"}}}
    reply = loop.run_until_complete(_request_async(port, cms))
    assert json.loads(reply["cms"]["content"]) == {"pong": True}
```

- `initialize_task_async()` only schedules the server, so the client retries until the port
  is bound instead of connecting once.
- The request is the full envelope `{"cms": {...}}` and needs `request.full-url`; the router
  matches it against handler routes to choose the context type.
- Teardown cancels every pending task on the app loop, which closes the listener. Without it
  the server keeps running into the next test.
- Always put a timeout (`asyncio.wait_for`) around the read, so a missing reply fails the test
  instead of hanging it.

## Pitfall: `asyncio.run` instead of the app loop

`from_options` creates or adopts an event loop and registers it in DI; on Windows it always
creates a new `ProactorEventLoop`. Synchronous handlers run in that loop's executor.
`asyncio.run(app.dispatch_async(context))` runs on a different, new loop, and the result
depends on the handler:

```text
async handler, asyncio.run -> 200 OK {"kind": "async"}
sync handler,  asyncio.run -> 500 Internal Server Error {"errorCode": null, "errorMessage": "Task <Task pending ...> got Future <Future pending ...> attached to a different loop"}
sync handler,  app loop    -> 200 OK {"kind": "sync"}
```

No exception is raised; the sync case only shows up as a 500 in the response. Always run
dispatches on the loop from `app.service_provider.get_service(asyncio.AbstractEventLoop)`, as
`run_dispatch` does.

See [architecture.md](architecture.md) for the request path these tests exercise and
[limitations.md](limitations.md) for known gaps.
