# Extending BasisEdge

BasisEdge 4.1 has five extension points: `Predicate` subclasses, hosted services
(`IHostedService`), application services in the DI container, the logger (`ILogger`), and
listeners (`IListener`). Each section has a complete example that runs against `bclib` 4.1.0,
with its output in comments. The last section lists the parts that look pluggable but are not.

The examples run requests through the dispatcher on the app's own event loop instead of
opening a port, so each one is a plain script. They share this helper, saved as
`local_dispatch.py` next to them (the same technique is covered in [testing.md](testing.md)):

```python
import asyncio
import json

from bclib.context import RESTfulContext
from bclib.listener.http.http_message import HttpMessage


def dispatch(app, url: str, method: str = "get", query: dict | None = None) -> dict:
    """Run one RESTful request through the app without a network listener."""
    cms = {"request": {"url": url, "methode": method}, "query": query or {}}
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    return loop.run_until_complete(app.dispatch_async(RESTfulContext(cms, app, HttpMessage(cms))))


def content(result: dict):
    return json.loads(result["cms"]["content"])
```

In a real service you register the same pieces and call `app.listening()`.

## Custom predicates

A predicate decides whether a handler runs. For one-off logic, an async function passed to
`app.callback(...)` is enough; see
[Custom callback predicate](../README.md#104-custom-callback-predicate). Write a `Predicate`
subclass when the rule is reused or takes parameters.

The contract is one method, `async def check_async(self, context) -> bool`. The base class
stores an optional dot-path expression and provides `self._evaluate_expression(context)`,
which walks it through attributes and dictionary keys: `context.query.code` reads
`context.query["code"]`. The leading `context.` is optional.

```python
from bclib import edge
from bclib.context import Context, RESTfulContext
from bclib.exception import UnauthorizedErr
from bclib.predicate import Predicate

from local_dispatch import content, dispatch


class StartsWith(Predicate):
    """Matches when the value at `expression` is a string starting with `prefix`."""

    def __init__(self, expression: str, prefix: str) -> None:
        super().__init__(expression)
        self.__prefix = prefix

    async def check_async(self, context: Context) -> bool:
        try:
            value = self._evaluate_expression(context)
        except (KeyError, AttributeError, TypeError):
            return False
        return isinstance(value, str) and value.startswith(self.__prefix)


class RequireApiKey(Predicate):
    """Rejects the request with 401 instead of falling through to the next handler."""

    def __init__(self, expected: str) -> None:
        super().__init__("context.query.key")
        self.__expected = expected

    async def check_async(self, context: Context) -> bool:
        try:
            value = self._evaluate_expression(context)
        except (KeyError, AttributeError, TypeError):
            value = None
        if value != self.__expected:
            raise UnauthorizedErr("missing or wrong key")
        return True


app = edge.from_options({"name": "predicate-demo"})


@app.restful_handler("api/orders", StartsWith("context.query.code", "EU-"), method="GET")
def eu_orders(context: RESTfulContext):
    return {"region": "eu", "code": context.query["code"]}


@app.restful_handler("api/orders", method="GET")
def other_orders():
    return {"region": "other"}


@app.restful_handler("api/admin", RequireApiKey("<api-key>"))
def admin():
    return {"admin": True}


print(content(dispatch(app, "api/orders", query={"code": "EU-17"})))  # {'region': 'eu', 'code': 'EU-17'}
print(content(dispatch(app, "api/orders", query={"code": "US-3"})))  # {'region': 'other'}
print(dispatch(app, "api/admin")["cms"]["webserver"]["headercode"])  # 401 Unauthorized
print(content(dispatch(app, "api/admin", query={"key": "<api-key>"})))  # {'admin': True}
```

How the dispatcher treats a predicate:

- Handlers of one context type are tried in registration order; within a handler, predicates
  are checked in order. The first `False` moves on to the next handler, so register the
  narrower handler first, as `eu_orders` is above.
- Raising a `ShortCircuitErr` subclass (`UnauthorizedErr`, `ForbiddenErr`, `BadRequestErr`, ...)
  stops dispatching and becomes the response; later handlers are not tried. See
  [Errors & Status Codes](../README.md#16-errors--status-codes).
- Any other exception becomes a 500 response. Catch lookup errors inside `check_async`.
- Only the built-in `Url` predicate (a route string, `app.url(...)`, `app.get(...)`, ...) feeds
  the router that picks the context type for an incoming URL. A custom predicate narrows a
  handler; it cannot route a URL that no handler's route matches.
- Custom predicates combine with built-in ones through `app.all(...)` and `app.any(...)`.

## Hosted services

A hosted service is a singleton with startup and shutdown hooks. Implement
`bclib.di.IHostedService`; `start_async` and `stop_async` both default to no-ops.

```python
import asyncio

from bclib import edge
from bclib.di import IHostedService

from local_dispatch import content, dispatch


class PriceFeed(IHostedService):
    """Refreshes an in-memory price table in the background."""

    def __init__(self) -> None:
        self.prices: dict[str, float] = {}
        self.ticks = 0
        self.__task: asyncio.Task | None = None

    async def start_async(self) -> None:
        self.prices = {"usd": 1.0}  # ready before any listener binds
        self.__task = asyncio.get_running_loop().create_task(self.__refresh_async())

    async def stop_async(self) -> None:
        self.__task.cancel()
        await asyncio.gather(self.__task, return_exceptions=True)
        print("stopped after", self.ticks, "ticks")

    async def __refresh_async(self) -> None:
        while True:
            await asyncio.sleep(0.05)
            self.ticks += 1
            self.prices["usd"] = 1.0 + self.ticks / 100


app = edge.from_options({"name": "hosted-demo", "logger": {"level": "WARNING"}})
app.service_provider.add_singleton(PriceFeed, is_hosted=True)


@app.restful_handler("api/price", method="GET")
def price(feed: PriceFeed):
    return {"usd": feed.prices["usd"], "ticks": feed.ticks}


# listening() runs these steps around its run loop; here they run one by one.
loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
loop.run_until_complete(app.initialize_task_async())  # starts hosted services
loop.run_until_complete(asyncio.sleep(0.3))
print(content(dispatch(app, "api/price")))  # {'usd': 1.05, 'ticks': 5}
loop.run_until_complete(app.service_provider.stop_hosted_services_async())  # stopped after 5 ticks
```

Lifecycle rules:

- `app.listening()` calls `initialize_task_async()`, which starts hosted services before any
  listener binds. On SIGINT or SIGTERM it calls `stop_async` on each one, then closes the
  listeners and cancels the remaining tasks.
- Order: services with `priority > 0` start first, highest first, then `priority == 0` in
  registration order. Shutdown runs in reverse.
- Startup awaits each `start_async`. Start long-running work as a task, as above.
- **Register each hosted service under its own type.** Startup resolves each hosted
  registration with `get_service(service_type)`, which returns the first registration of that
  type: two registrations under `IHostedService` start the first class twice and never the
  second.
- A hosted service is an ordinary singleton, so handlers can inject it (`feed` above).
- A test that only calls `dispatch_async` never starts hosted services.

## Application services through DI

Any class can be a service. Constructor and handler parameters are resolved from their type
annotations, and a handler parameter named like a URL segment (`sku` below) receives that
segment. Registration and lifetimes are covered in
[Dependency Injection](../README.md#11-dependency-injection); this example combines an
interface, configuration injected into the constructor, and a scoped object.

```python
from abc import ABC, abstractmethod

from bclib import edge
from bclib.options import IOptions

from local_dispatch import content, dispatch


class IStockStore(ABC):
    @abstractmethod
    async def quantity_async(self, sku: str) -> int: ...


class MemoryStockStore(IStockStore):
    def __init__(self, options: IOptions["inventory"]) -> None:
        self.__items: dict[str, int] = dict(options.get("seed", {}))

    async def quantity_async(self, sku: str) -> int:
        return self.__items.get(sku, 0)


class RequestAudit:
    """Scoped: one instance per request."""

    def __init__(self) -> None:
        self.events: list[str] = []


app = edge.from_options({"name": "service-demo",
                         "inventory": {"seed": {"A-1": 7}}})
app.service_provider.add_singleton(IStockStore, MemoryStockStore)
app.service_provider.add_scoped(RequestAudit)


@app.restful_handler("api/stock/:sku", method="GET")
async def stock(sku: str, store: IStockStore, audit: RequestAudit):
    audit.events.append(f"read {sku}")
    return {"sku": sku, "qty": await store.quantity_async(sku), "audit": audit.events}


print(content(dispatch(app, "api/stock/A-1")))  # {'sku': 'A-1', 'qty': 7, 'audit': ['read A-1']}
print(content(dispatch(app, "api/stock/B-2")))  # {'sku': 'B-2', 'qty': 0, 'audit': ['read B-2']}
```

Every request opens its own scope, so each one gets a fresh `RequestAudit`.

**The first registration wins.** Registering a type again adds a second implementation
instead of replacing the first: `get_service(T)` and plain injection return the first, and
`list[T]` returns all (see
[dependency-injection-multiple-implementations.md](dependency-injection-multiple-implementations.md)).
To use a fake in tests, choose the implementation before registering it, for example through
an app factory parameter as shown in [testing.md](testing.md). The one exception is a framework
default such as the console `ILogger`, which your registration replaces (next section).

## Replacing the logger

`from_options` registers `ConsoleLogger` as a replaceable default for `ILogger`. An explicit
`add_singleton(ILogger, MyLogger)`, made after `from_options`, removes that default, so every
`ILogger[...]` resolved from then on, in handlers and in your services, is your class. The
implementation subclasses `ILogger[T]` (a `logging.Logger`) and receives the generic argument
as `generic_type_args`:

```python
import logging
import sys
from typing import Type, TypeVar

from bclib import edge
from bclib.logger import ILogger
from bclib.options import AppOptions

from local_dispatch import content, dispatch

T = TypeVar("T")


class JsonLinesLogger(ILogger[T]):
    """Writes one JSON object per record to standard output."""

    def __init__(self, options: AppOptions, generic_type_args: tuple[Type, ...] = None):
        category = generic_type_args[0] if generic_type_args else None
        # ILogger["Orders"] arrives as a ForwardRef, ILogger[SomeClass] as the class
        name = getattr(category, "__forward_arg__", getattr(category, "__name__", "app"))
        super().__init__(name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '{"logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'))
        self.addHandler(handler)
        self.setLevel(logging.INFO)


app = edge.from_options({"name": "logger-demo"})
app.service_provider.add_singleton(ILogger, JsonLinesLogger)  # after from_options


@app.restful_handler("api/orders/:id", method="GET")
def get_order(id: str, logger: ILogger["Orders"]):
    logger.info("order %s read", id)
    return {"id": id}


print(content(dispatch(app, "api/orders/7")))
# {"logger": "Orders", "level": "INFO", "message": "order 7 read"}
# {'id': '7'}
```

- `list[ILogger]` returns only your logger; the console logger is no longer registered.
- The dispatcher resolves its own logger inside `from_options`, before your registration, so its
  messages (dispatch errors, unmatched requests, shutdown) still go to the console logger
  configured by the `logger` option.
- Register it once. A second explicit registration is an ordinary additional implementation,
  and the first one wins.

## Custom listeners

A listener receives requests from a transport and hands them to the dispatcher:

- it implements `IListener.initialize_task()`, which schedules its work on the app's loop and
  returns without blocking;
- each request is a `Message` that also implements `ICmsBaseMessage` (exposes the CMS dict)
  and `IResponseBaseMessage` (receives the reply through `set_response_async`);
- each message goes to `IMessageHandler.on_message_receive_async`.

This listener reads requests from an in-process `asyncio.Queue`:

```python
import asyncio

from bclib import edge
from bclib.context import RESTfulContext
from bclib.dispatcher import IMessageHandler
from bclib.listener import ICmsBaseMessage, IListener, IResponseBaseMessage, Message

from local_dispatch import content


class QueueMessage(Message, ICmsBaseMessage, IResponseBaseMessage):
    def __init__(self, cms: dict, reply: asyncio.Future) -> None:
        self.__cms, self.__reply = cms, reply

    @property
    def cms_object(self) -> dict:
        return self.__cms

    async def set_response_async(self, cms_object: dict) -> None:
        self.__reply.set_result(cms_object)


class QueueListener(IListener):
    """Feeds (cms, future) pairs from an in-process queue into the dispatcher."""

    def __init__(self, message_handler: IMessageHandler, loop: asyncio.AbstractEventLoop) -> None:
        self._message_handler = message_handler
        self.__loop = loop
        self.queue: asyncio.Queue = asyncio.Queue()

    def initialize_task(self) -> None:
        self.__task = self.__loop.create_task(self.__consume_async())

    async def close_async(self) -> None:  # listening() calls it on shutdown when present
        self.__task.cancel()

    async def __consume_async(self) -> None:
        while True:
            cms, reply = await self.queue.get()
            await self._message_handler.on_message_receive_async(QueueMessage(cms, reply))


app = edge.from_options({"name": "listener-demo", "logger": {"level": "WARNING"}})


@app.restful_handler("jobs/:name", method="POST")
def run_job(context: RESTfulContext):
    return {"job": context.url_segments["name"], "accepted": True}


listener = app.service_provider.create_instance(QueueListener)
app.add_listener(listener)


async def main() -> None:
    await app.initialize_task_async()  # listening() does this, then runs the loop forever
    reply = asyncio.get_running_loop().create_future()
    request = {"full-url": "local/jobs/rebuild", "url": "jobs/rebuild", "methode": "post"}
    await listener.queue.put(({"cms": {"request": request}}, reply))
    print(content(await asyncio.wait_for(reply, 5)))  # {'job': 'rebuild', 'accepted': True}
    await listener.close_async()


app.service_provider.get_service(asyncio.AbstractEventLoop).run_until_complete(main())
```

Before writing one:

- `create_instance` builds the listener with its constructor dependencies resolved from DI.
- `cms_object` is the full envelope `{"cms": {"request": {...}}}`, and `request` must carry
  `full-url`. The context type is chosen by matching the path of `full-url` against registered
  handler routes; unlike the built-in HTTP, TCP, WebSocket and RabbitMQ messages, a custom
  message has no fallback type, so an unmatched URL gets an error reply.
- If processing fails before a context exists, the dispatcher still replies through
  `set_response_async`, with a 500 or the status of a `ShortCircuitErr`. For a message without
  `IResponseBaseMessage` it re-raises.
- **`add_listener` replaces the configured listeners.** The `http`, `tcp` and `rabbitmq`
  listeners from the options load only when none was added by hand. To keep them, add them
  first:

  ```python
  from bclib.listener import IListenerFactory

  for configured in app.service_provider.get_service(IListenerFactory).load_listeners():
      app.add_listener(configured)
  app.add_listener(listener)
  ```

Configuring the built-in listeners is covered in
[Listeners](../README.md#18-listeners-http--tcp--rabbit--ssl).

## What is not an extension point

- **Cache backends.** The dispatcher builds its cache manager from the `cache` option through
  a fixed factory that knows only `"memory"` (any other type raises `ValueError`), so a
  `CacheManager` subclass has no supported way in. Use the built-in cache
  ([Cache](../README.md#15-cache)) or register your own cache client as a DI service.
- **Dispatcher and context factory.** Both are created inside `from_options`, with no
  supported way to supply your own.

See [architecture.md](architecture.md) for how the pieces fit together and
[limitations.md](limitations.md) for known gaps.
