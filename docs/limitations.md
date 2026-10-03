# Limitations in 4.0.1

Known gaps and defects in bclib 4.0.1 that affect application code or operations, each with what
to do instead. Upgrading from 3.x is covered at the end.

## Routing

- **The `router` option is not read.** The context type (REST, web, WebSocket, source) is chosen
  from the URL patterns of the registered handlers ([architecture.md](architecture.md)). A URL that
  matches no pattern becomes an `HttpContext`, so a REST-only app answers unknown paths with an
  HTML 404. *Instead:* register a catch-all REST handler last:

  ```python
  from bclib.context import RESTfulContext
  from bclib.exception import NotFoundErr

  @app.restful_handler()
  async def not_found(context: RESTfulContext):
      raise NotFoundErr(f"no route for {context.url}")
  ```

- **Context selection uses the first unanchored match.** Patterns are tested with `re.search`
  against `host:port/path`, grouped by context type in registration order. With
  `restful_handler("users")` and `web_handler("users/profile")`, a request for `/users/profile`
  is routed as REST and returns 404. *Instead:* give each context type its own prefix (for
  example `api/` for REST only) and avoid route strings that occur inside other routes.

- **No CORS support.** There is no CORS middleware and no automatic `OPTIONS` reply; a preflight
  request gets 404 unless a handler matches `OPTIONS`. `HttpHeaders.add_cors_headers(context)`
  only sets `Access-Control-Allow-Origin: *` and `Access-Control-Allow-Headers`. *Instead:* see
  [security.md](security.md#cors).

- **No health or metrics endpoint.** *Instead:* add a handler; see
  [deployment.md](deployment.md#health-and-monitoring).

## Connections and cache

- **Connection services are per request.** `IMongoConnection` is scoped and `IRabbitConnection`
  and `IRestfulConnection` are transient, so injecting them into handlers creates new clients per
  request and nothing closes them. *Instead:* hold them in a singleton service
  ([deployment.md](deployment.md#performance)).
- **`IMongoConnection.close()` does not close the async client.** It calls
  `AsyncMongoClient.close()` without awaiting it, which only produces a `RuntimeWarning`.
  *Instead:* close the client you used directly: `await connection.async_client.close()` or
  `connection.client.close()`.
- **The REST client is minimal.** `IRestfulConnection` has no retries, returns only the body
  (parsed JSON, else text) without status or headers, and reports HTTP errors as a plain
  `Exception` whose message contains the status. *Instead:* pass `raise_for_status=False` and
  inspect the body, or use aiohttp directly for status, headers, streaming and retries.
- **RabbitMQ messages are acknowledged even when the handler fails.** The dispatcher turns
  handler exceptions into error responses, so the consumer always acknowledges. Messages are
  processed one at a time per listener. *Instead:* catch failures in the handler and republish
  or dead-letter explicitly; scale with more listeners or processes.
- **`@app.cache` ignores arguments and does not support coroutines.** It stores one value per
  function; on an `async def` the second call fails with
  `RuntimeError: cannot reuse already awaited coroutine`. *Instead:* use it only on synchronous
  functions without parameters, and `app.cache_manager.add_or_update` / `get_cache` for keyed
  values.
- **The RabbitMQ cache signaler cannot start.** `"cache": {"signaler": {"type": "rabbit"}}`
  fails during `from_options` with `no running event loop`
  (`bclib/cache/signaler/rabbit_signaler.py`). *Instead:* consume the invalidation queue
  yourself (a `rabbitmq` listener and `rabbit_handler`) and call `app.cache_manager.reset(keys)`.

## WebSockets

- The upgrade is accepted before any handler is matched, and there is no `Origin` check.
  Authenticate in the handler and close unauthorised sessions.
- The heartbeat interval (30 s) and aiohttp's message limits are fixed; no option changes them.
- Sessions and groups live in process memory. Broadcasts do not reach clients connected to
  another process. *Instead:* relay through RabbitMQ to each process.

## Process and platform

- **Graceful shutdown does not run on Linux with an HTTP listener.** `SIGTERM` exits with status
  1 without calling hosted services' `stop_async`. A workaround is in
  [deployment.md](deployment.md#graceful-shutdown).
- **The HTTP server is not stopped cleanly.** On shutdown its cleanup raises
  `AttributeError: '_HttpListener__ssl_options'`, so `site.stop()` and `runner.cleanup()` are
  skipped; sockets are released only when the process exits.
- **`edge.from_list` fails on Python 3.14**, which `python_requires` allows: it calls
  `asyncio.get_event_loop()` with no loop set. It also does not restart or signal children.
  *Instead:* use a process manager, or run `from_list` on 3.13.
- **`from_options` parses `sys.argv`.** `-n <name>` overrides `name` and `-m` hides the banner.
  The long form `--Name` is silently ignored, and an unrecognised flag prints a `getopt` error
  and stops parsing, so a `-n` after it is lost. Do not give your own script `-n` or `-m` flags,
  and put Edge's flags first.
- **ODBC on Linux needs system packages.** `pyodbc` fails to import without unixODBC and a driver
  ([deployment.md](deployment.md#operating-system-notes)).
- **No TCP-specific handler.** Requests from the TCP listener are dispatched to
  `web_handler`/`restful_handler` by URL; `TcpContext` exists but is never created.

## Logging and errors

- **`logger` is shared by two services.** `ConsoleLogger` reads `level`/`format` from it, while
  `ILogService` requires `logger.type`. With `"logger": {"level": "INFO"}`, injecting
  `ILogService` fails with `Type property not set for logger!` and the handler gets a 500.
  *Instead:* do not inject `ILogService` unless you configure a schema logger.
- **A custom `ILogger` is not used.** `from_options` registers the console logger first, and the
  first registration wins, so `add_singleton(ILogger, MyLogger)` changes nothing that handlers
  receive (the repository's `examples/logger/custom_logger.py` shows this pattern, but it has no
  effect). *Instead:* configure Python `logging` handlers and formatters directly.
- **`log_error` has no effect.** Tracebacks in responses are controlled by `error_log`
  ([configuration-reference.md](configuration-reference.md)).
- **The request log always shows the method as `none`.** `ContextFactory` reads `method`, but the
  CMS request carries `methode`.
- **Unmatched requests log a full traceback at `ERROR`.** Filter `HandlerNotFoundErr` in your log
  pipeline or add the catch-all handler above.
- **Top-level `ssl` is ignored.** TLS options belong inside each `http` entry
  ([README §18](../README.md#18-listeners-http--tcp--rabbit--ssl)).

## Upgrading from 3.x

**Stale modules in the 4.0.0 wheel.** The 4.0.0 package on PyPI shipped 31 modules left over from
older versions alongside the 4.0 code, for example:

```
bclib.context.web_context
bclib.dispatcher.routing_dispatcher
bclib.listener.socket_listener
```

4.0.1 removes them, so importing them now fails with `ModuleNotFoundError`. Move such code to
the 4.0 API below: import contexts from `bclib.context` and get the dispatcher from
`edge.from_options`.

**Name map.**

| 3.x | 4.0 |
|-----|-----|
| `@app.restful_action(...)` | `@app.restful_handler(...)` |
| `@app.web_action(...)` with `WebContext` | `@app.web_handler(...)` with `HttpContext` |
| `@app.client_source_action(...)` | `@app.client_source_handler(...)` |
| `@app.client_source_member_action(...)` | `@app.client_source_member_handler(...)` |
| `@app.server_source_action(...)` | `@app.server_source_handler(...)` |
| `@app.server_source_member_action(...)` | `@app.server_source_member_handler(...)` |
| `@app.rabbit_action(...)` | `@app.rabbit_handler(...)` |
| `@app.socket_action(...)` | no equivalent; TCP requests reach `web_handler`/`restful_handler` |
| `@app.named_pipe_action(...)` | no equivalent; named-pipe listeners were removed |
| `RoutingDispatcher`, `DevServerDispatcher`, `SocketDispatcher`, `NamedPipeDispatcher`, `EndpointDispatcher` | one `Dispatcher` (typed as `IDispatcher`) |
| `SocketListener` | `TcpListener` (`bclib.listener.tcp`) |
| `app.event_loop` | `app.service_provider.get_service(asyncio.AbstractEventLoop)` |
| `listening(with_block=False)` | no equivalent; `listening()` takes no arguments and blocks |
| `NoLogger` | no class; without a `logger` section, `ILogService` discards events |

Handlers in 4.0 receive services and URL segments by parameter type and name
([README §8](../README.md#8-handlers)); a handler that only takes `context` keeps working.

## Related

- [deployment.md](deployment.md)
- [security.md](security.md)
- [configuration-reference.md](configuration-reference.md)
- [README §24](../README.md#24-troubleshooting)
