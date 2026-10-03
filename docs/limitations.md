# Limitations in 4.1.0

Known gaps in bclib 4.1.0 that affect application code or operations, each with what to do
instead. Upgrading from 3.x is covered at the end.

## Routing

- **The `router` option is not read.** The context type (REST, web, WebSocket, source) is chosen
  from the URL patterns of the registered handlers ([architecture.md](architecture.md#choosing-the-context-the-router)).
  A URL that matches no pattern becomes an `HttpContext`, so a REST-only app answers unknown
  paths with an HTML 404. *Instead:* register a catch-all REST handler last:

  ```python
  from bclib.context import RESTfulContext
  from bclib.exception import NotFoundErr

  @app.restful_handler()
  async def not_found(context: RESTfulContext):
      raise NotFoundErr(f"no route for {context.url}")
  ```

- **Overlapping routes of different context types are not ranked by specificity.** Concrete
  patterns are tried grouped by context type, in the order the context types were first
  registered. With `restful_handler("api/:*rest")` registered before `web_handler("api/users")`,
  a request for `/api/users` becomes a `RESTfulContext` and never reaches the web handler.
  *Instead:* give each context type its own prefix (for example `api/` for REST only).

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
- **The REST client is minimal.** `IRestfulConnection` has no retries, returns only the body
  (parsed JSON, else text) without status or headers, and reports HTTP errors as a plain
  `Exception` whose message contains the status. *Instead:* pass `raise_for_status=False` and
  inspect the body, or use aiohttp directly for status, headers, streaming and retries.
- **RabbitMQ messages are acknowledged even when the handler fails.** The dispatcher turns
  handler exceptions into error responses, so the consumer always acknowledges. Messages are
  processed one at a time per listener. *Instead:* catch failures in the handler and republish
  or dead-letter explicitly; scale with more listeners or processes.
- **`@app.cache` does not store `None`.** A cached function that returns `None` runs again on
  every call. *Instead:* return an empty value (`[]`, `{}`) for "no data".

## WebSockets

- The upgrade is accepted before any handler is matched, and there is no `Origin` check.
  Authenticate in the handler and close unauthorised sessions.
- The heartbeat interval (30 s) and aiohttp's message limits are fixed; no option changes them.
- Sessions and groups live in process memory. Broadcasts do not reach clients connected to
  another process. *Instead:* relay through RabbitMQ to each process.

## Process and platform

- **In-flight requests are cancelled on shutdown, not drained.** *Instead:* stop routing traffic
  to the process before sending `SIGTERM` ([deployment.md](deployment.md#graceful-shutdown)).
- **`edge.from_list` is not a supervisor.** It does not restart a child that exits and does not
  forward `SIGTERM` to the children. *Instead:* use a process manager in production
  ([deployment.md](deployment.md#process-model)).
- **`from_options` parses `sys.argv`.** `-n <name>` or `--Name <name>` overrides `name`, and
  `-m` or `--Multi` hides the banner. An unrecognised flag prints a `getopt` error and stops
  parsing, so a `-n` after it is lost. Do not give your own script `-n` or `-m` flags, and put
  Edge's flags first.
- **ODBC on Linux needs system packages.** `pyodbc` fails to import without unixODBC and a driver
  ([deployment.md](deployment.md#operating-system-notes)).
- **No TCP-specific handler.** Requests from the TCP listener are dispatched to
  `web_handler`/`restful_handler` by URL; `TcpContext` exists but is never created.

## Logging and errors

- **`log_error` has no effect.** Tracebacks in responses are controlled by `error_log`
  ([configuration-reference.md](configuration-reference.md)).
- **A listener configuration error surfaces as a `TypeError`.** For example, a `rabbitmq` entry
  without `url` fails at `listening()` with `RabbitListener.__init__() missing 3 required
  positional arguments`. *Instead:* read the `ERROR` log line just before it, which carries the
  real cause ([configuration-reference.md](configuration-reference.md#reading-configuration-errors)).
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

4.0.1 and later do not contain them, so importing them fails with `ModuleNotFoundError`. Move
such code to the 4.x API below: import contexts from `bclib.context` and get the dispatcher from
`edge.from_options`.

**Name map.**

| 3.x | 4.x |
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
| `NoLogger` | no class; without a schema logger (`logger.type`), `ILogService` discards events |

Handlers in 4.x receive services and URL segments by parameter type and name
([README §8](../README.md#8-handlers)); a handler that only takes `context` keeps working.

## Related

- [deployment.md](deployment.md)
- [security.md](security.md)
- [configuration-reference.md](configuration-reference.md)
- [README §24](../README.md#24-troubleshooting)
