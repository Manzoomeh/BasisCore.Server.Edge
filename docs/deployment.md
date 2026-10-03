# Deployment

Running a BasisEdge 4.0.1 service in production. Listener options are in
[README §18](../README.md#18-listeners-http--tcp--rabbit--ssl), every option key is in
[configuration-reference.md](configuration-reference.md), and the request pipeline is in
[architecture.md](architecture.md).

## Installing

BasisEdge needs **Python 3.13 or later** (`python_requires=">=3.13"` in `setup.py`).

**From PyPI**

```bash
pip install bclib==4.0.1
```

This resolves the runtime dependencies from the ranges declared in `setup.py`
(`aiohttp>=3.14,<4`, `aio-pika>=10.1,<11`, `pika>=1.4,<2`, `pymongo>=4.18,<5`, `pyodbc>=5.3,<6`,
`cryptography>=50.0,<51`, `certifi>=2026.7.22`). pip may pick newer minor releases than the ones
the package was tested with.

**Pinned**

The repository's `requirements.txt` pins every runtime package, including transitive ones, at
the versions the test suite ran against. To get those exact versions with the PyPI package, use
it as a constraints file:

```bash
pip install bclib==4.0.1 -c requirements.txt
```

Use the pinned set for anything you deploy ([README §3](../README.md#3-install)). All seven
dependencies are installed even if you never use MongoDB, RabbitMQ or ODBC; the clients are
imported only when used.

## Process model

**One process, one event loop.** `edge.from_options(...)` creates a single asyncio loop and
registers it in the DI container; `app.listening()` runs that loop until shutdown. Every listener
(`http`, `tcp`, `rabbitmq`, and lists of each), every `async def` handler and every hosted service
runs on that loop, in one thread. Two consequences follow:

- One process uses at most one CPU core for Python work. To use more cores, run more processes.
- Anything that blocks inside an `async def` handler stalls every connection in the process.

**Several processes on one host: `edge.from_list`.** `from_list` is a launcher. For each entry
it appends `-n <name>` and `-m` to the argument list, runs it with `subprocess.run` on a thread
pool (one thread per entry), and waits until all of them exit:

```python
import sys
from bclib import edge

edge.from_list({
    "rest-a": [sys.executable, "services/rest_a.py"],
    "rest-b": [sys.executable, "services/rest_b.py"],
})
```

In each child, `from_options` reads `-n` into `options["name"]` (it prefixes the request log
lines) and `-m` suppresses the start-up banner. The children share nothing: each has its own
loop, DI container, in-memory cache and WebSocket sessions, and each must bind its own port.
`examples/multi_server/` runs two services this way.

`from_list` is a development convenience, not a supervisor: it does not restart a child that
exits, does not forward `SIGTERM` to the children, does not load-balance (put a reverse proxy or
the BasisCore web server in front), and fails at start-up under Python 3.14
([limitations.md](limitations.md#process-and-platform)). In production, run one Edge process per
unit of your process manager (systemd, a container orchestrator, a Windows service wrapper).

## Docker

The repository's `Dockerfile` builds an image that runs `examples/docker/main.py`:

1. a builder stage creates `/opt/venv` from `python:3.13-slim` and installs `requirements.txt`;
2. the runtime stage copies that venv, then copies the whole build context to `/app`
   (`.dockerignore` excludes `.git`, `__pycache__`, `*.pyc` and virtualenv folders) and
   `examples/docker` to `/app/code`;
3. a `bclib.pth` file adds `/app` to the venv's `sys.path`, so `bclib` is imported from the
   copied source, not installed as a package;
4. `CMD ["python", "code/main.py"]`.

Build and run it from the repository root:

```bash
docker build -t bclib-edge-sample .
docker run --rm -p 9181:9181 bclib-edge-sample
```

The sample binds `"http": "localhost:9181"`. Inside a container that is the container's own
loopback interface, so the published port is **not reachable from the host** as shipped. Change
the endpoint to `0.0.0.0:9181` in `examples/docker/main.py` before building. The same applies to
every service you containerise: bind `0.0.0.0` and publish the port. The `Dockerfile` has no
`EXPOSE` line, so `-p` must always be given explicitly.

For your own service, a smaller image installs the package instead of copying the repository:

```dockerfile
FROM python:3.13-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir bclib==4.0.1 -c requirements.txt
COPY app/ ./app/
EXPOSE 8080
CMD ["python", "app/main.py"]
```

Here `requirements.txt` is the pinned file from the BasisEdge repository, and `app/main.py` calls
`edge.from_options({"http": "0.0.0.0:8080", ...})` and `app.listening()`. Add the ODBC packages
below if the service uses SQL Server.

`docker stop` sends `SIGTERM`. Read [Graceful shutdown](#graceful-shutdown) before relying on
cleanup code in containers.

## Operating-system notes

**Event loop.** When no `loop` is passed to `from_options`, Edge creates an
`asyncio.ProactorEventLoop` on Windows and installs it as the current loop
(`bclib/di/__init__.py`). The IOCP-based proactor is used because the selector loop is limited
to 64 sockets on Windows. On Linux and macOS, Edge uses the thread's current loop, or creates
one, which is the standard selector loop. Pass `loop=` only if you need a specific loop
implementation; Edge then uses it unchanged on every platform.

**ODBC.** `pyodbc` is installed on every platform, but it is imported only when the legacy
`DbManager` opens a `sql` connection (`bclib/db_manager/odbc_db.py`). The Linux wheel does not
bundle the ODBC driver manager: importing it on a plain `python:3.13-slim` image fails with
`ImportError: libodbc.so.2`. Install unixODBC and a driver for your database:

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends unixodbc \
 && rm -rf /var/lib/apt/lists/*
# then install your database's ODBC driver
# (for SQL Server, Microsoft's msodbcsql18 package from Microsoft's repository)
```

On Windows, the SQL Server ODBC driver named in your connection string must be installed on the
host.

## Logging in production

Edge has two separate logging features. Both read the top-level `logger` key, which matters for
the second one (see [limitations.md](limitations.md#logging-and-errors)).

**Diagnostic logging: `ILogger[T]`.** The default implementation, `ConsoleLogger`, is a standard
`logging.Logger` that writes to standard error. Options under `logger`:

| Key | Default | Effect |
|-----|---------|--------|
| `level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL` |
| `format` | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | standard `logging` format string |
| `use_colors` | `true` | ANSI colours; switched off automatically when stdout is not a TTY |
| `async_logging` | `true` | writes through a `QueueHandler`; a background thread does the I/O and is flushed at exit |
| `queue_size` | `-1` | queue bound for async logging; `-1` is unlimited |

For JSON output or log files, attach standard `logging` handlers or formatters to Python's
logging system at start-up. Registering a second `ILogger` implementation has no effect in
4.0.1: the console logger registered by `from_options` is the one that gets injected
([limitations.md](limitations.md#logging-and-errors)). See also [README §14](../README.md#14-logger).

**Request logging: `log_request`.** On by default. Each request produces one `INFO` line from
`ContextFactory`:

```
my-app: (RESTfulContext::AD_HOC) - 1 none 127.0.0.1:8080/api/orders?page=2
```

The fields are the app `name`, context type, message type, a per-process request counter, the
method (always `none` in 4.0.1, see [limitations.md](limitations.md#logging-and-errors)) and the
URL with its query string. If clients send tokens or personal data in query strings, set
`"log_request": false` or filter the `ContextFactory` logger.

**Errors.** Every exception that reaches the dispatcher is logged at `ERROR` with a traceback,
including `HandlerNotFoundErr` for an unmatched URL. A scanner probing random paths therefore
produces one traceback per request. `log_error` has no effect. `error_log: true` adds the
traceback to the response body; keep it off in production ([security.md](security.md)).

**Event logging: `ILogService`.** For business events sent to a schema-based log collector, set
`logger.type` to `schema.restful` or `schema.rabbit` and inject `ILogService`. Without `logger`,
`ILogService` accepts calls and discards them.

## Health and monitoring

4.0.1 has no built-in health endpoint, metrics endpoint or readiness hook. Besides the log lines
above, hosted services ([extending.md](extending.md)) give you start and stop hooks: `start_async`
runs before any listener binds and `stop_async` during graceful shutdown.

Add a health handler yourself, on a path no other handler uses:

```python
from bclib.context import RESTfulContext

@app.restful_handler("healthz", method="GET")
async def healthz(_: RESTfulContext):
    return {"status": "ok"}
```

It shows that the loop is responsive, not that downstream systems are up. A service that listens
only on `tcp` for the BasisCore web server can add an `http` listener on a private port for
probes; both share one dispatcher.

## Graceful shutdown

`app.listening()` installs handlers for `SIGTERM` and `SIGINT` with `signal.signal`. When one
fires, the dispatcher:

1. calls `stop_async` on hosted services, in reverse start order;
2. calls `close_async` on listeners that have one (the RabbitMQ listener), with a 3-second
   timeout;
3. cancels every other task on the loop (HTTP and TCP servers, in-flight requests, WebSocket
   sessions, background tasks) and waits up to 5 seconds;
4. stops and closes the loop, and `listening()` returns.

In-flight requests are cancelled, not drained. Put a load balancer drain period in front of the
stop signal if requests must complete.

**Linux with an HTTP listener.** The HTTP listener starts aiohttp's `AppRunner` with
`handle_signals=True`, which replaces the dispatcher's handlers once the server starts. A
`SIGTERM` or `SIGINT` then raises aiohttp's `GracefulExit` (a `SystemExit`) out of
`listening()`: the process exits with status 1, hosted services' `stop_async` is never called,
and the loop is closed with tasks still pending. This is what `docker stop` triggers. Windows is
not affected because the proactor loop does not support `add_signal_handler`.

Until this is fixed, a hosted service can put the dispatcher's handlers back after aiohttp has
replaced them:

```python
import asyncio
import signal

from bclib.di import IHostedService


class KeepEdgeSignalHandlers(IHostedService):
    """Restores the dispatcher's SIGTERM/SIGINT handlers after the HTTP listener replaces them."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def start_async(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}

        async def watch():
            for _ in range(100):  # up to ~10 s after start-up
                await asyncio.sleep(0.1)
                if signal.getsignal(signal.SIGTERM) is not saved[signal.SIGTERM]:
                    for sig, handler in saved.items():
                        self._loop.remove_signal_handler(sig)
                        signal.signal(sig, handler)
                    return

        self._loop.create_task(watch())


app.service_provider.add_singleton(KeepEdgeSignalHandlers, KeepEdgeSignalHandlers, is_hosted=True)
```

With it, `SIGTERM` runs the full sequence above and the process exits with status 0.

## Performance

**Async and sync handlers.** Each decorator inspects the handler once, at registration.
An `async def` handler is awaited on the event loop. A plain `def` handler is run with
`loop.run_in_executor(None, ...)` (`bclib/di/injection_plan.py`), that is, on the loop's default
`ThreadPoolExecutor`, whose size is `min(32, os.cpu_count() + 4)`. So:

- Prefer `async def` with async clients (aiohttp, `AsyncMongoClient`, aio-pika) for I/O.
- A `def` handler with blocking I/O (pyodbc, the synchronous `pymongo` client, `requests`) is
  safe for the loop, but concurrency is capped by the pool. Size the pool before
  `listening()` if you rely on many concurrent blocking handlers:

  ```python
  import asyncio
  from concurrent.futures import ThreadPoolExecutor

  loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
  loop.set_default_executor(ThreadPoolExecutor(max_workers=64, thread_name_prefix="edge-sync"))
  ```

- Never call blocking code inside an `async def` handler. Either make the handler `def`, or
  offload the call explicitly with `run_in_executor`.
- `def` handlers run on worker threads; state shared between them must be thread-safe.
- `app.run_in_background(fn, *args)` follows the same rule: coroutine functions become tasks,
  plain functions go to the default executor.

**CPU-bound work.** Threads do not help with pure-Python CPU work because of the GIL. Use a
process pool from an async handler, keeping the worker function in a separate module:

```python
from concurrent.futures import ProcessPoolExecutor
from cpu_work import fib  # plain function in its own module

pool = ProcessPoolExecutor(max_workers=2)
loop = app.service_provider.get_service(asyncio.AbstractEventLoop)

@app.restful_handler("fib/:n", method="GET")
async def fib_handler(context: RESTfulContext):
    n = int(context.url_segments["n"])
    return {"n": n, "fib": await loop.run_in_executor(pool, fib, n)}
```

On Windows, workers re-import the main module, so keep `app.listening()` under
`if __name__ == "__main__":`. For sustained CPU load, run more Edge processes.

**Connection reuse.** The connection services are not process-wide singletons:

| Service | Lifetime | What a new instance creates |
|---------|----------|-----------------------------|
| `IMongoConnection[key]` | scoped (one per request) | a `MongoClient` / `AsyncMongoClient` with its own pool, on first use |
| `IRabbitConnection[key]` | transient (one per injection) | a robust aio-pika connection and channel, on first use |
| `IRestfulConnection[key]` | transient (one per injection) | an aiohttp `ClientSession` with its own connector, on first use |

Injecting them straight into handlers opens new clients and sockets per request, and nothing
closes them at the end of the request. Inject them once into a singleton service instead, and
inject that service into handlers:

```python
from bclib.connections import IMongoConnection, IRestfulConnection

class OrderStore:
    def __init__(self, db: IMongoConnection["database.orders"],
                 billing: IRestfulConnection["billing_api"]):
        self.db = db              # one client and pool for the process
        self.billing = billing    # one ClientSession for the process

app.service_provider.add_singleton(OrderStore)

@app.restful_handler("api/orders/:id", method="GET")
async def get_order(id: str, store: OrderStore):
    return await store.db.get_async_collection("orders").find_one({"_id": id}, {"_id": 0})
```

To close them on shutdown, make the singleton a hosted service and, in `stop_async`, await
`close_async()` on REST and RabbitMQ connections. For MongoDB, close the client you used directly
(`await db.async_client.close()` or `db.client.close()`) rather than `db.close()`
([limitations.md](limitations.md#connections-and-cache)). The legacy `DbManager` opens a new
pyodbc/sqlite/Mongo connection on every `open_*_connection` call; keep those calls in `def`
handlers so they run on the executor.

**Cache.** `"cache": {"type": "memory"}` enables a per-process in-memory cache; without it,
`@app.cache` does nothing ([README §15](../README.md#15-cache)). Use it for results that are
expensive and identical for every caller, such as lookup tables and configuration fetched from
another service. Points to plan for:

- `@app.cache` stores one value per decorated function and ignores arguments; it only suits
  functions with no parameters. For per-key data use `app.cache_manager.add_or_update(key, data,
  life_time)` and `get_cache(key)`.
- It wraps synchronous functions only. Do not put it on an `async def`.
- Each process, including each `from_list` child, has its own copy. Defaults clean expired
  entries every 12 hours and reset the whole cache every 24 hours; set `clean_interval` and
  `reset_interval` (seconds, `0` disables) to match your data.

**RabbitMQ consumers.** A `rabbitmq` listener processes messages from its queue one at a time
and acknowledges each after the handler returns. Throughput per queue is therefore bounded by
handler latency. To process a queue in parallel, run several processes, or several entries in the
`rabbitmq` list for the same queue.

## Related

- [configuration-reference.md](configuration-reference.md): every option key
- [security.md](security.md): TLS, exposure of the TCP endpoint, error details
- [limitations.md](limitations.md): known gaps in 4.0.1
- [README §19](../README.md#19-multi-process-hosts) and [README §24](../README.md#24-troubleshooting)
