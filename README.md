# BasisEdge

**BasisCore.Server.Edge** (`bclib`) — Python edge gateway for [BasisCore](https://basiscore.com).

BasisEdge sits at the **edge of your network**: you build REST APIs, dbsource handlers, WebSocket services, TCP endpoints, and RabbitMQ consumers that talk to the BasisCore webserver, while databases, message brokers, and secrets stay in your own environment (on-prem or private cloud).

| | |
|--|--|
| Package | `bclib` |
| Entry point | `from bclib import edge` |
| Python | **3.13+** |
| License | MIT |

---

## Ship your Edge services on BasisPanel

BasisEdge is built and maintained by **Manzoomeh Negaran**, and it is already in production with a
growing community of independent developers who deliver their own services on it — and who help
us shape and improve the platform with every release.

**Now you can take your services live without running your own servers.** If you have a **Banian**
account on [basispanel.ai](https://basispanel.ai), you can upload the services you build with
BasisEdge directly to your panel and run them on Manzoomeh's managed infrastructure.

- **Build your backend your way.** Write any logic you need in Python — REST APIs, dbsource
  handlers, WebSocket and TCP services, RabbitMQ consumers — with no restrictions imposed by the
  hosting side.
- **Deploy straight from your panel.** Upload your service to BasisPanel and it runs on
  Manzoomeh's infrastructure: no servers to provision and no separate hosting to manage.
- **Launch the whole product in one place.** Pair your backend with BasisPanel's AI-powered
  front-end tools and take your project from first endpoint to full launch on a single platform.

Have a question? The Manzoomeh team is here to help — reach us through
[manzoomeh.com](https://manzoomeh.com) or [basispanel.ai](https://basispanel.ai).

---

## Table of Contents

1. [Why BasisEdge](#1-why-basisedge)
2. [Core Concepts](#2-core-concepts)
3. [Install](#3-install)
4. [Quick Start](#4-quick-start)
5. [Creating an App](#5-creating-an-app)
6. [Options Reference](#6-options-reference)
7. [Request Lifecycle](#7-request-lifecycle)
8. [Handlers](#8-handlers)
9. [Contexts](#9-contexts)
10. [Routing & Predicates](#10-routing--predicates)
11. [Dependency Injection](#11-dependency-injection)
12. [Configuration (`IOptions`)](#12-configuration-ioptions)
13. [Connections](#13-connections)
14. [Logger](#14-logger)
15. [Cache](#15-cache)
16. [Errors & Status Codes](#16-errors--status-codes)
17. [Static Files](#17-static-files)
18. [Listeners (HTTP / TCP / Rabbit / SSL)](#18-listeners-http--tcp--rabbit--ssl)
19. [Multi-process Hosts](#19-multi-process-hosts)
20. [Client / Server Source (dbsource)](#20-client--server-source-dbsource)
21. [Common Patterns](#21-common-patterns)
22. [Examples & Tests](#22-examples--tests)
23. [API Map](#23-api-map)
24. [Troubleshooting](#24-troubleshooting)

---

## 1. Why BasisEdge

Modern products need a thin, stable layer between the public web and private systems. BasisEdge is that layer:

- **API gateway** — expose REST/JSON endpoints for BasisCore pages and external clients
- **DBsource bridge** — implement BasisCore `dbsource` commands without opening the database to the public internet
- **Realtime** — WebSocket and TCP listeners for chat, notifications, device protocols
- **Messaging** — consume and publish RabbitMQ (queue or exchange) with the same DI model
- **Security boundary** — keep connection strings, certificates, and business logic behind the edge

You write Python handlers; the framework handles listening, routing, CMS message shape, DI scopes, and response wrapping.

---

## 2. Core Concepts

```
Client / BasisCore
        │
        ▼
   Listener (HTTP | TCP | Rabbit)
        │  Message
        ▼
   Dispatcher (edge app)
        │  Context + DI scope
        ▼
   Handler (your code)
        │  return value / raise Err
        ▼
   Response (CMS / JSON / HTML / ack)
```

| Concept | Meaning |
|---------|---------|
| **edge** | Module with `from_options`, `from_config`, `from_list` |
| **Dispatcher (`app`)** | Runtime: routes messages, runs handlers, owns DI and cache |
| **Listener** | Binds a port or queue; converts bytes/HTTP into a `Message` |
| **Context** | Per-request object (`RESTfulContext`, `HttpContext`, …) with URL, body, query, DI scope |
| **Handler** | Your function/coroutine registered with a decorator |
| **Predicate** | Rule that decides if a handler matches this request |
| **ServiceProvider** | DI container (singleton / scoped / transient) |

`edge.from_options(...)` builds the dispatcher and registers default services (logger, options, connections, listener factory).  
`app.listening()` creates listeners from config and starts the event loop.

---

## 3. Install

```bash
# runtime
pip install -r requirements.txt

# or install the package (wheel / editable)
pip install .
pip install -e ".[dev]"
```

**Runtime dependencies (summary):** `aiohttp`, `aio-pika`, `pika`, `pymongo`, `pyodbc`, `cryptography`, `certifi`.

`requirements.txt` pins the exact tested versions, including transitive dependencies, for reproducible
installs; `setup.py` declares compatible ranges for the package. See the header of `requirements.txt`
to update them.

**Dev / tests:**

```bash
pip install -r requirements-dev.txt
pytest
```

Requires **Python 3.13+**.

---

## 4. Quick Start

Create `main.py`:

```python
from bclib import edge
from bclib.context import RESTfulContext

app = edge.from_options({
    "name": "hello-api",
    "http": "localhost:8080",
    "router": "restful",
    "log_request": True,
    "log_error": True,
})

@app.restful_handler("api/hello", method="GET")
def hello(context: RESTfulContext):
    return {"message": "Hello BasisEdge", "url": context.url}

@app.restful_handler("api/users/:id", method="GET")
def get_user(context: RESTfulContext):
    user_id = context.url_segments["id"]
    return {"id": user_id, "name": f"user-{user_id}"}

if __name__ == "__main__":
    app.listening()
```

Run and call:

```bash
python main.py

curl http://localhost:8080/api/hello
curl http://localhost:8080/api/users/42
```

What happens:

1. `from_options` creates DI, registers logger/options/connections, returns a `Dispatcher`
2. Decorators register handlers in an internal lookup keyed by context type
3. `listening()` starts an HTTP listener on `localhost:8080`
4. Each request becomes a `RESTfulContext`; matching predicates run; your function returns a dict → JSON CMS response

---

## 5. Creating an App

### 5.1 From a dictionary (recommended)

```python
from bclib import edge

app = edge.from_options({
    "name": "my-app",
    "http": "0.0.0.0:8080",
    "router": "restful",
    "log_request": True,
    "log_error": True,
})
```

Optional: pass an existing asyncio loop:

```python
import asyncio
loop = asyncio.new_event_loop()
app = edge.from_options(options, loop=loop)
```

### 5.2 From a JSON file

```python
# Directory + default file name host.json  →  ./config/host.json
app = edge.from_config("./config")

# Custom file name in that directory
app = edge.from_config("./config", "production.json")

# Explicit .json file path
app = edge.from_config("./config/host.json")
```

`from_config` only loads JSON and calls `from_options`.

### 5.3 What `from_options` registers for you

Without writing extra code you already get:

- Root `ServiceProvider` + event loop
- Default console `ILogger[T]`
- `AppOptions` + transient `IOptions[T]` factory
- Connection factories (Mongo / Rabbit / RESTful)
- Log service hooks
- Listener factory (used later by `listening()`)
- Dispatcher with cache manager

### 5.4 When to call `listening()`

| Situation | Call `listening()`? |
|-----------|---------------------|
| Real server / consumer | Yes |
| Unit tests / `dispatch_async` only | No |
| Library that only builds `app` for another host | No |

---

## 6. Options Reference

Common top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `name` | str | App name (logging / splash) |
| `http` | str \| dict \| list | HTTP endpoint(s), optional SSL |
| `tcp` | str \| dict \| list | TCP endpoint(s) |
| `rabbitmq` | dict \| list | RabbitMQ consumer config(s) |
| `router` | str \| dict | Default router mode or path map |
| `log_request` | bool | Log incoming requests |
| `log_error` | bool | Log handler errors |
| `cache` | dict | e.g. `{"type": "memory", "clean_interval": 60}` |
| `logger` | dict | Logger options for `ILogger` |
| `database` | dict | Nested Mongo (or other) connection sections |
| `ssl` | dict | Can also nest under `http` object |

### Router styles

```python
# Simple: everything is restful
{"router": "restful"}

# Map URL patterns to context kinds
{"router": {
    "restful": ["api/*"],
    "web": ["*"],
    "rabbit": [{"url": "amqp://...", "queue": "tasks"}]
}}
```

### Full sample `host.json`

```json
{
  "name": "my-app",
  "http": "0.0.0.0:8080",
  "router": "restful",
  "log_request": true,
  "log_error": true,
  "database": {
    "users": {
      "connection_string": "mongodb://localhost:27017",
      "database_name": "users_db",
      "timeout": 5000
    }
  },
  "rabbitmq": {
    "tasks": {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "task_queue",
      "durable": true
    }
  },
  "external_api": {
    "base_url": "https://api.example.com",
    "timeout": 30,
    "headers": { "Authorization": "Bearer ..." },
    "ssl_verify": true
  },
  "cache": {
    "type": "memory",
    "clean_interval": 60,
    "reset_interval": 120
  },
  "logger": {
    "level": "INFO"
  }
}
```

---

## 7. Request Lifecycle

1. **Listener** accepts HTTP / TCP / Rabbit delivery  
2. Builds a **Message** (`HttpMessage`, `RabbitMessage`, …)  
3. **ContextFactory** chooses context type from message + router  
4. Dispatcher creates a **scoped DI** container on the context  
5. Looks up handlers for `type(context)`  
6. Runs **predicates** in order; first match wins  
7. **InjectionPlan** resolves handler parameters (context, services, URL segments)  
8. Handler return value is wrapped (`generate_response`) or Rabbit returns as-is  
9. Exceptions become error responses via `generate_error_response`  

For REST, a Python `dict` return becomes JSON inside the BasisCore CMS envelope.

---

## 8. Handlers

Handlers are plain functions or `async` coroutines. Register them with decorators on `app`.

| Decorator | Context type | Typical use |
|-----------|--------------|-------------|
| `restful_handler` | `RESTfulContext` | JSON APIs |
| `web_handler` | `HttpContext` | HTML / form pages |
| `websocket_handler` | `WebSocketContext` | Realtime WebSocket |
| `rabbit_handler` | `RabbitContext` | Queue / exchange consume |
| `client_source_handler` | `ClientSourceContext` | Client dbsource command |
| `client_source_member_handler` | `ClientSourceMemberContext` | Per-member of client source |
| `server_source_handler` | `ServerSourceContext` | Server dbsource command |
| `server_source_member_handler` | `ServerSourceMemberContext` | Per-member of server source |
| `handler` | inferred from type hints | Universal / auto router |

### 8.1 Signature flexibility

```python
# Context only
@app.restful_handler("api/a", method="GET")
def a(context: RESTfulContext):
    return {"url": context.url}

# Services only (no context parameter)
@app.restful_handler("api/b", method="GET")
def b(logger: ILogger["B"]):
    logger.info("b")
    return {"ok": True}

# Mix + URL segment as typed param (string/int conversion via ValueStrategy)
@app.restful_handler("api/users/:id", method="GET")
def c(context: RESTfulContext, logger: ILogger["C"], id: int):
    return {"id": id}
```

Sync and async handlers are both supported.

### 8.2 REST examples

```python
@app.restful_handler("api/items", method="GET")
def list_items(context: RESTfulContext):
    return {"items": []}

@app.restful_handler("api/items", method="POST")
def create_item(context: RESTfulContext):
    # context.body is parsed JSON when Content-Type is application/json
    return {"created": True, "body": context.body}

@app.restful_handler("api/items/:id", method=["GET", "PUT"])
def item(context: RESTfulContext):
    return {"id": context.url_segments["id"], "method": context.cms["request"]["methode"]}
```

### 8.3 Web (HTML)

```python
from bclib.context import HttpContext

@app.web_handler("home", method="GET")
def home(context: HttpContext):
    name = context.query.get("name", "guest")
    return f"<h1>Hello {name}</h1>"
```

### 8.4 Universal `handler`

Inspects the annotated context type and routes to the matching decorator family:

```python
@app.handler("auto", method="GET")
def auto_rest(context: RESTfulContext):
    return {"mode": "auto-rest"}

@app.handler("page", method="GET")
def auto_web(context: HttpContext):
    return "<p>auto-web</p>"
```

### 8.5 RabbitMQ handler

```python
from bclib.context import RabbitContext

@app.rabbit_handler()
def on_task(context: RabbitContext):
    print("host", context.host)
    print("queue", context.queue)
    print("body", context.raw_message)
    print("routing_key", context.message.routing_key)
    return {"processed": True}
```

### 8.6 WebSocket handler

```python
from bclib.context import WebSocketContext

@app.websocket_handler("ws/chat/:room")
async def chat(context: WebSocketContext):
    room = context.url_segments.get("room")
    text = context.message.text
    await context.session.send_text({"room": room, "echo": text})
    # broadcast:
    # await context.session_manager.broadcast({"room": room, "text": text})
```

See runnable samples under `examples/websocket/` and `examples/websocket/chat/`.

---

## 9. Contexts

Every handler receives (or can inject) a context. Important fields:

### Shared (most CMS contexts)

| Property | Description |
|----------|-------------|
| `url` | Request URL path |
| `url_segments` | Captured `:id` style segments (dict-like) |
| `query` | Query string |
| `form` | Form body |
| `cms` | Raw CMS object |
| `services` | **Scoped** DI provider for this request |
| `dispatcher` | Parent dispatcher |

### `RESTfulContext`

| Property | Description |
|----------|-------------|
| `body` | Parsed JSON or form dict |
| `mime` | Defaults to `application/json` |

### `RabbitContext`

| Property | Description |
|----------|-------------|
| `host` / `queue` | Broker host and queue |
| `raw_message` | Body as UTF-8 text |
| `message` | `RabbitMessage` (headers, routing_key, …) |

### `WebSocketContext`

| Property | Description |
|----------|-------------|
| `session` | Current `WebSocketSession` |
| `session_manager` | All sessions / broadcast |
| `message` | `WebSocketMessage` (text/binary/connect/…) |

Access DI from a context:

```python
db = context.services.get_service(IMongoConnection["database.users"])
```

---

## 10. Routing & Predicates

A handler runs only if **all** its predicates match. You can pass a route string and `method=` to the decorator, or pass predicate objects built on `app`.

### 10.1 Decorator style

```python
@app.restful_handler("users/:id", method="GET")
def get_user(context: RESTfulContext):
    return {"id": context.url_segments["id"]}
```

`:id` (and similar) populate `context.url_segments`.

### 10.2 Predicate helper style

`Dispatcher` inherits `PredicateHelper`, so helpers are on `app`:

```python
@app.restful_handler(app.get("users/:id"))
def get_user(context: RESTfulContext):
    return {"id": context.url_segments["id"]}

@app.restful_handler(
    app.url("posts/:id"),
    app.is_get(),
    app.has_value("context.query.filter"),
)
def filtered(context: RESTfulContext):
    return {
        "id": context.url_segments["id"],
        "filter": context.query.get("filter"),
    }
```

### 10.3 Predicate catalog

| Helper | Meaning |
|--------|---------|
| `url(pattern)` | Match path; fill `url_segments` |
| `get/post/put/delete/options(pattern)` | `url` + HTTP method |
| `is_get` / `is_post` / `is_put` / `is_delete` / `is_options` | Method only |
| `equal(expr, value)` | Equality on a context path |
| `not_equal(expr, value)` | Inequality |
| `has_value(expr)` | Path exists and is non-empty |
| `in_list(expr, *items)` | Membership |
| `between` / `greater_than` / `less_than` / … | Comparisons |
| `match(expr, pattern)` | Pattern match |
| `all(*predicates)` | AND |
| `any(*predicates)` | OR |
| `callback(async_fn)` | Custom async predicate |

Expression paths look like: `context.query.role`, `context.cms.request.methode`.

> Wire format uses the spelling **`methode`** (not `method`) inside CMS request objects.

### 10.4 Custom callback predicate

```python
async def is_admin(context):
    return context.query.get("role") == "admin"

@app.restful_handler("admin/stats", app.callback(is_admin))
def stats(context: RESTfulContext):
    return {"ok": True}
```

---

## 11. Dependency Injection

### 11.1 Basics

`from_options` creates a root `ServiceProvider`. Each request context gets a **child scope**. Handlers and constructors are injected by type annotations.

```python
from abc import ABC, abstractmethod
from bclib import edge
from bclib.context import RESTfulContext
from bclib.logger import ILogger

class IGreeter(ABC):
    @abstractmethod
    def greet(self, name: str) -> str: ...

class Greeter(IGreeter):
    def greet(self, name: str) -> str:
        return f"Hello, {name}"

app = edge.from_options({"http": "localhost:8080", "router": "restful"})
app.service_provider.add_singleton(IGreeter, Greeter)

@app.restful_handler("api/greet/:name", method="GET")
def greet(context: RESTfulContext, greeter: IGreeter, logger: ILogger["GreetApi"]):
    logger.info("greet called")
    return {"text": greeter.greet(context.url_segments["name"])}

app.listening()
```

You can also import the container type directly:

```python
from bclib.di import ServiceProvider, ServiceLifetime, create_service_container
```

### 11.2 Lifetimes

| API | Lifetime | Typical use |
|-----|----------|-------------|
| `add_singleton(T, Impl)` | One instance for the process | Config, clients, loggers |
| `add_scoped(T, Impl)` | One instance per request scope | Unit of work, request state |
| `add_transient(T, Impl)` | New instance every resolve | Lightweight helpers |

```python
sp = app.service_provider
sp.add_singleton(IGreeter, Greeter)
sp.add_scoped(IUnitOfWork, UnitOfWork)
sp.add_transient(IHelper, Helper)
```

### 11.3 Factory registration

```python
sp.add_singleton(
    IEmailSender,
    factory=lambda sp, **kwargs: SmtpSender(
        sp.get_service(IOptions["smtp"]),
        sp.get_service(ILogger["Smtp"]),
    ),
)
```

### 11.4 Pre-created instance

```python
logger = ConsoleLogger(...)
sp.add_singleton(ILogger, instance=logger)
```

### 11.5 Multiple implementations

Register the same interface several times:

```python
sp.add_singleton(IListener, HttpListener)
sp.add_singleton(IListener, TcpListener)
sp.add_singleton(IListener, RabbitListener)

first = sp.get_service(IListener)              # HttpListener (first)
all_listeners = sp.get_service(list[IListener])  # all three
```

Constructor injection of `list[IListener]` also receives every registration.

Full guide: [`docs/dependency-injection-multiple-implementations.md`](docs/dependency-injection-multiple-implementations.md).

### 11.6 Manual resolve & scopes

```python
scope = app.service_provider.create_scope()
uow = scope.get_service(IUnitOfWork)
# ...
scope.clear_scope()
```

---

## 12. Configuration (`IOptions`)

The options dict passed to `from_options` is stored as **`AppOptions`**. Nested sections are resolved with a generic key:

```python
from bclib.options import AppOptions, IOptions

root = app.service_provider.get_service(AppOptions)
# entire dict

users_db = app.service_provider.get_service(IOptions["database.users"])
# → {"connection_string": "...", "database_name": "..."}

tasks = app.service_provider.get_service(IOptions["rabbitmq.tasks"])
```

Dots navigate nested dictionaries (`database` → `users`). This is the same key you use on connection generics: `IMongoConnection["database.users"]`.

In handlers/services:

```python
class ReportService:
    def __init__(self, opts: IOptions["reporting"]):
        self.enabled = opts.get("enabled", False)
```

---

## 13. Connections

Modern connections are registered by `from_options` via `add_connection_services`. You inject interfaces with a **config key** as the generic argument. Initialization is **lazy** (no network until first use).

### 13.1 MongoDB

**Config**

```json
"database": {
  "users": {
    "connection_string": "mongodb://localhost:27017",
    "database_name": "users_db",
    "timeout": 5000,
    "max_pool_size": 100
  }
}
```

**Usage**

```python
from bclib.connections.mongo import IMongoConnection

class UserRepo:
    def __init__(self, db: IMongoConnection["database.users"]):
        self.users = db.get_collection("users")

    def find(self, user_id: str):
        return self.users.find_one({"_id": user_id})
```

Also supports async client APIs on the same connection object (`get_async_collection`, …).

### 13.2 RabbitMQ (`aio-pika`)

**Config (queue mode)**

```json
"rabbitmq": {
  "tasks": {
    "url": "amqp://guest:guest@localhost:5672/",
    "queue": "task_queue",
    "durable": true
  }
}
```

**Config (exchange mode)**

```json
"rabbitmq": {
  "events": {
    "url": "amqp://guest:guest@localhost:5672/",
    "exchange": "domain.events",
    "exchange_type": "topic",
    "routing_key": "user.created",
    "durable": true
  }
}
```

**Usage**

```python
from bclib.connections.rabbit import IRabbitConnection

class TaskPublisher:
    def __init__(self, bus: IRabbitConnection["rabbitmq.tasks"]):
        self.bus = bus

    async def enqueue(self, payload: dict):
        await self.bus.publish(payload)
```

More detail: `examples/rabbit/` and `examples/rabbit/README.md`.

### 13.3 RESTful HTTP client

**Config**

```json
"external_api": {
  "base_url": "https://api.example.com",
  "timeout": 30,
  "headers": { "X-App": "edge" },
  "ssl_verify": true,
  "ssl_cert_path": null
}
```

**Usage**

```python
from bclib.connections.restful import IRestfulConnection

class RemoteUsers:
    def __init__(self, api: IRestfulConnection["external_api"]):
        self.api = api

    async def list_async(self):
        resp = await self.api.get_async("/users")
        return await resp.json()
```

### 13.4 Legacy `DbManager`

Older samples still use `context.dispatcher.db_manager.open_*_connection(...)`. Prefer the new `bclib.connections.*` + DI style for new code; see `MIGRATION_DbContext_to_Connection.md` if you are migrating.

---

## 14. Logger

Default registration: `ILogger[T]` → console logger. The generic argument is a **category name** (like .NET `ILogger<T>`):

```python
from bclib.logger import ILogger

@app.restful_handler("api/ping", method="GET")
def ping(logger: ILogger["PingApi"]):
    logger.debug("debug")
    logger.info("ping")
    logger.warning("slow")
    logger.error("failed")
    return {"ok": True}
```

Configure via options key `logger` (level, formatting, …).  
Custom loggers: see `examples/logger/custom_logger.py`.

---

## 15. Cache

### 15.1 Enable in-memory cache

```python
app = edge.from_options({
    "http": "localhost:8080",
    "router": "restful",
    "cache": {
        "type": "memory",
        "clean_interval": 60,
        "reset_interval": 120
    },
})
```

Without `cache` (or without `type`), a no-op cache manager is used.

### 15.2 Decorator

```python
@app.cache()
def expensive_report():
    return {"rows": [...]}
```

### 15.3 Manual API

```python
cm = app.cache_manager
cm.add_or_update("demo", {"v": 1}, life_time=300)
value = cm.get_cache("demo")
cm.reset(["demo"])   # or reset() for all
cm.clean()           # drop expired
```

Runnable demo: `examples/cache/simple.py`.

---

## 16. Errors & Status Codes

Raise framework exceptions to short-circuit with a proper HTTP status. The dispatcher catches them and builds an error response.

```python
from bclib.exception import (
    BadRequestErr,      # 400
    UnauthorizedErr,    # 401
    ForbiddenErr,       # 403
    NotFoundErr,        # 404
    MethodNotAllowedErr,# 405
    InternalServerErr,  # 500
    HandlerNotFoundErr, # 404 specialized
)

@app.restful_handler("api/secure", method="GET")
def secure(context: RESTfulContext):
    token = context.query.get("token")
    if not token:
        raise UnauthorizedErr("missing token")
    if token != "secret":
        raise ForbiddenErr("invalid token")
    return {"ok": True}
```

Base type: `ShortCircuitErr(status_code, error_code=-1, message=None, data=None)`.

Uncaught exceptions are logged (if `log_error`) and converted via `context.generate_error_response`.

Samples: `examples/exceptions/`.

---

## 17. Static Files

```python
from pathlib import Path
from bclib.utility import StaticFileHandler

public = Path(__file__).parent / "public"
handler = StaticFileHandler(
    base_dir=str(public),
    allowed_extensions={".html", ".css", ".js", ".png", ".jpg", ".svg"},
    enable_index=True,                 # serve index.html for directories
    index_files=["index.html", "index.htm"],
    url_prefix="/static",              # strip this prefix from URL
)
app.add_static_handler(handler)
```

Security: path traversal outside `base_dir` is rejected; extension whitelist is optional.

Sample: `examples/static_file/`.

---

## 18. Listeners (HTTP / TCP / Rabbit / SSL)

Listeners are **not** started in `from_options`. They are created in `listening()` from options.

| Options key | Listener | Notes |
|-------------|----------|-------|
| `http` | `HttpListener` | string `"host:port"` or dict / list of dicts |
| `tcp` | `TcpListener` | binary framed TCP |
| `rabbitmq` | `RabbitListener` | one consumer per config entry |

### 18.1 HTTP string form

```python
{"http": "localhost:8080"}
{"http": "0.0.0.0:8080"}
```

### 18.2 HTTP dict + SSL (PEM)

```python
{
  "http": {
    "endpoint": "0.0.0.0:443",
    "ssl": {
      "certfile": "cert.pem",
      "keyfile": "key.pem"
    }
  },
  "router": "web"
}
```

### 18.3 HTTP dict + SSL (PFX / P12)

```python
{
  "http": {
    "endpoint": "0.0.0.0:443",
    "ssl": {
      "pfxfile": "server.pfx",
      "password": "secret"
    }
  },
  "router": "web"
}
```

Samples with local certs: `examples/http/https_pem.py`, `examples/http/https_pfx.py`, `examples/http/certs/`.

### 18.4 Multiple HTTP endpoints

```python
{
  "http": [
    "localhost:8080",
    {"endpoint": "localhost:8443", "ssl": {"certfile": "...", "keyfile": "..."}}
  ]
}
```

### 18.5 Rabbit consumer

```python
{
  "rabbitmq": {
    "url": "amqp://guest:guest@localhost:5672/",
    "queue": "edge-tasks",
    "durable": true
  }
}
```

Or a list of queue configs. Pair with `@app.rabbit_handler()`.

### 18.6 TCP

```python
{"tcp": "localhost:3000"}
```

See `examples/endpoint/server_and_client.py`.

---

## 19. Multi-process Hosts

Run several Edge processes from one launcher:

```python
from bclib import edge

edge.from_list({
    "api": ["python", "examples/multi_server/simple_rest_a.py"],
    "web": ["python", "examples/multi_server/simple_rest_b.py"],
})
```

Each entry is started in a thread pool via `subprocess`; `-n <name>` and `-m` flags are appended for multi-instance splash behavior.

---

## 20. Client / Server Source (dbsource)

BasisCore pages often call **dbsource** commands (HTML-like XML). Edge exposes:

- **Client source** — command arrives over HTTP form (`command`, `dmnid`)
- **Server source** — command pushed/server-driven

Pattern:

1. `@app.client_source_handler()` returns a data payload  
2. Framework iterates `command.member` nodes  
3. Each member is dispatched to `@app.client_source_member_handler()` (optionally filtered by predicates on `context.member.name`)

```python
@app.client_source_handler()
def source(context: ClientSourceContext):
    return [{"id": 1, "name": "Ada"}]

@app.client_source_member_handler(app.equal("context.member.name", "list"))
def list_member(context: ClientSourceMemberContext):
    return context.data
```

Samples: `examples/client_source/`, `examples/server_source/`, `examples/share_source/`.

---

## 21. Common Patterns

### 21.1 Service layer + REST

```python
sp = app.service_provider
sp.add_singleton(IUserService, UserService)

@app.restful_handler("api/users/:id", method="GET")
def get_user(id: int, users: IUserService):
    return users.get(id)
```

### 21.2 Publish after write

```python
@app.restful_handler("api/orders", method="POST")
async def create_order(context: RESTfulContext, bus: IRabbitConnection["rabbitmq.events"]):
    order = context.body
    await bus.publish({"type": "order.created", "order": order})
    return {"status": "queued"}
```

### 21.3 Auth gate via predicate + error

```python
async def require_token(context):
    return bool(context.query.get("token"))

@app.restful_handler("api/private", app.callback(require_token))
def private(context: RESTfulContext):
    if context.query.get("token") != "secret":
        raise ForbiddenErr()
    return {"secret": True}
```

### 21.4 Background work

```python
# fire-and-forget on dispatcher loop
app.dispatch_in_background(some_context)
app.run_in_background(blocking_fn, arg1, arg2)
```

---

## 22. Examples & Tests

| Path | Role |
|------|------|
| [`examples/`](examples/README.md) | Runnable samples (REST, WS, Rabbit, DI, SSL, …) |
| [`tests/`](tests/) | Automated unit suite |
| [`docs/`](docs/) | Deep feature notes (e.g. multi-impl DI) |

```bash
# samples
python examples/restful/hello.py
python examples/http/simple.py
python examples/websocket/simple.py

# unit tests
pytest
pytest -v tests/test_handlers.py
```

---

## 23. API Map

| Symbol | Role |
|--------|------|
| `bclib.edge.from_options` | Create app from dict |
| `bclib.edge.from_config` | Load JSON → `from_options` |
| `bclib.edge.from_list` | Multi-process launcher |
| `app.listening()` | Bind listeners + run loop |
| `app.service_provider` | Root DI |
| `app.cache_manager` | Cache facade |
| `app.*_handler(...)` | Register handlers |
| `app.url` / `app.get` / … | Predicates |
| `bclib.di.ServiceProvider` | DI container API |
| `bclib.options.IOptions[T]` | Typed config slices |
| `bclib.connections.mongo.IMongoConnection[T]` | Mongo |
| `bclib.connections.rabbit.IRabbitConnection[T]` | Rabbit |
| `bclib.connections.restful.IRestfulConnection[T]` | HTTP client |
| `bclib.logger.ILogger[T]` | Logging |
| `bclib.exception.*` | HTTP short-circuit errors |
| `bclib.utility.StaticFileHandler` | Static files |

Version: `import bclib; bclib.__version__` (current **4.0.0**).

---

## 24. Troubleshooting

| Symptom | Likely cause | What to try |
|---------|--------------|-------------|
| `from bclib.di import ServiceProvider` fails | Old install / incomplete package | Reinstall `4.0.0+`; ensure `bclib/di/__init__.py` exports it |
| `from_config("./config")` looks in CWD for `host.json` | Old bug | Use current tree (`dir / file_name` join) |
| Handler never runs | Predicates / wrong context type | Log `context.url` and `methode`; simplify to `@app.restful_handler()` |
| DI param is `None` | Type not registered or wrong generic key | `sp.is_registered(T)`; check `IOptions["a.b"]` path |
| Mongo/Rabbit “hangs” on first call | First lazy connect | Check connection string / broker up |
| SSL won’t start | Bad cert paths | Use paths relative to process CWD or absolute; see `examples/http/certs/` |
| `cache` option crashes on startup | Plain dict without DictEx wrap | Fixed in 4.0; upgrade if you see `'dict' object has no attribute 'has'` |
| Event loop errors in tests | Mixing `asyncio.run` with app loop | Use the loop from `app.service_provider.get_service(asyncio.AbstractEventLoop)` |

---

## License

MIT — see [`LICENCE`](LICENCE).
