# Configuration reference

Every key that BasisEdge 4.0 reads from the options dictionary, with its type, default, the
module that reads it and what it does. The options dictionary is the `dict` you pass to
`edge.from_options(...)`, or the parsed `host.json` that `edge.from_config(...)` loads (see
[README: From a JSON file](../README.md#52-from-a-json-file)).

For the narrative tour of the same keys, see
[README: Options reference](../README.md#6-options-reference). This page is the exact list.

## How options are consumed

There are two ways a key gets read:

1. **By the framework.** A fixed set of top-level keys (`http`, `tcp`, `rabbitmq`, `cache`,
   `logger`, ...) is read by framework classes. Those keys are listed below.
2. **By your services.** Any other section is yours. Inject it with `IOptions["section.sub"]`,
   or pass the same key to a connection interface such as `IMongoConnection["database.users"]`
   (see [README: Configuration](../README.md#12-configuration-ioptions) and
   [README: Connections](../README.md#13-connections)). Dots walk nested dictionaries; the
   lookup falls back to a case-insensitive match (`bclib/utility/dict_resolver.py`). A
   missing section resolves to an empty `IOptions`.

Listeners are built from the options only when `app.listening()` runs. `from_options` itself
does not open ports, so a wrong certificate path or a malformed `rabbitmq` entry is reported
at `listening()`, not at `from_options`.

There is no environment-variable expansion: values are used exactly as written. To keep secrets
out of `host.json`, see [security.md](security.md#secrets-in-configuration).

## Top-level keys

| Key | Type | Default | Read by | Meaning |
|-----|------|---------|---------|---------|
| `name` | str | `None` | `bclib/dispatcher/dispatcher.py`, `bclib/context/context_factory.py` | Application name; prefixed to request log lines. Overridden by the `-n` / `--Name` command-line argument (`bclib/edge.py`). |
| `http` | str, dict or list | absent: no HTTP listener | `bclib/listener/listener_factory.py` | One HTTP/HTTPS (and WebSocket) listener per entry. See [`http` entries](#http-entries). |
| `tcp` | str, dict or list | absent: no TCP listener | `bclib/listener/listener_factory.py` | One binary-framed TCP listener per entry, used by the BasisCore web server. See [`tcp` entries](#tcp-entries). |
| `rabbitmq` | dict or list | absent: no consumer | `bclib/listener/listener_factory.py` | One RabbitMQ consumer per entry. See [`rabbitmq` entries](#rabbitmq-entries). |
| `log_request` | bool | `true` | `bclib/context/context_factory.py` | Log one `INFO` line per incoming request: name, context type, request id, URL. |
| `error_log` | bool | `false` | `bclib/context/cms_base_context.py` | Append the Python traceback to every error response. Development only; see [security.md](security.md#what-error-responses-expose). |
| `cache` | dict | absent: no-op cache | `bclib/dispatcher/dispatcher.py`, `bclib/cache/factory.py` | Result cache for `@app.cache`. See [`cache`](#cache). |
| `logger` | dict | absent: defaults below | `bclib/logger/console_logger.py`, `bclib/log_service/log_service.py` | Console logger settings, and the schema log service. See [`logger`](#logger). |
| `settings` | dict | absent: no named connections | `bclib/db_manager/db_manager.py` | Named connections for the legacy `IDbManager`. See [`settings`](#settings-legacy-dbmanager). |

Any other top-level key is ignored by the framework and is available to your code through
`IOptions`.

## `http` entries

`http` may be a single entry or a list of entries. Each entry is a string or a dictionary
(`bclib/listener/http/http_listener.py`).

**String form.** `"host:port"`, for example `"localhost:8080"`. A missing port means `80`
(`bclib/listener/endpoint.py`). IPv6 literals are not supported, because the string is split
on `:`.

**Dictionary form.**

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `endpoint` | str or dict | required | `"host:port"`, or `{"host": ..., "port": ...}` with defaults `"localhost"` and `80`. |
| `http` | str or dict | none | Used as the endpoint when `endpoint` is absent. |
| `ssl` | dict | none: plain HTTP | TLS settings for this listener only. See below. |
| `config` | dict | `{}` | Settings passed to the `aiohttp` application. See below. |

**`ssl`** (per listener; a top-level `ssl` key is not read):

| Key | Type | Meaning |
|-----|------|---------|
| `certfile` | str | PEM certificate (chain). When present, `keyfile` is required. |
| `keyfile` | str | PEM private key. |
| `pfxfile` | str | PKCS#12 bundle. Used only when `certfile` is absent. |
| `password` | str | PKCS#12 password. Required with `pfxfile`. |

Paths are opened relative to the process working directory. An `ssl` dictionary that contains
neither `certfile` nor `pfxfile` still switches the listener to TLS, with no certificate, so
every handshake fails. [security.md](security.md#tls-on-http-listeners) describes what happens
when a path is wrong.

**`config`**:

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `client_max_size` | int (bytes) | `1048576` (1 MiB) | Largest accepted request body, multipart included. Larger bodies get `413`. |
| `handler_args` | dict | none | Keyword arguments for aiohttp's request handler, for example `max_field_size` (largest header line, bytes) or `keepalive_timeout` (seconds). |
| `middlewares` | list | `()` | aiohttp middleware callables. Only usable from Python, not from JSON. |
| `router` | aiohttp router | `None` | Passed through to `aiohttp.web.Application`. Leave unset; it is not the request router. |

## `tcp` entries

`tcp` may be a single entry or a list (`bclib/listener/tcp/tcp_listener.py`).

| Form | Example | Defaults |
|------|---------|----------|
| String | `"127.0.0.1:1564"` | port `80` if omitted |
| Dictionary | `{"endpoint": "127.0.0.1:1564"}` or `{"endpoint": {"host": "127.0.0.1", "port": 1564}}` | `host` `"127.0.0.1"`, `port` `3000` |

The TCP listener has no TLS and no authentication. Bind it to loopback or a private interface;
see [security.md](security.md#keep-the-tcp-endpoint-private) and
[basiscore-integration.md](basiscore-integration.md).

## `rabbitmq` entries

`rabbitmq` is one consumer dictionary or a list of them. Each one is read by
`bclib/connections/rabbit/rabbit_connection.py`, which the listener extends.

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `url` | str | required | AMQP URL, for example `amqp://guest:guest@localhost:5672/`. |
| `queue` | str | none | Queue mode: consume this queue. Exactly one of `queue` / `exchange` is required. |
| `exchange` | str | none | Exchange mode: bind to this exchange. |
| `routing_key` | str | `""` | Binding key in exchange mode. |
| `exchange_type` | str | `"topic"` | `topic`, `direct`, `fanout` or `headers`. |
| `durable` | bool | `false` | Declare the queue / exchange durable. |
| `exclusive` | bool | `false` | Declare the queue exclusive. |
| `auto_delete` | bool | `false` | Declare the queue / exchange auto-delete. |
| `passive` | bool | `false` | Only check that the queue / exchange exists. |
| `retry_delay` | int (seconds) | `10` | Wait between reconnect attempts. |

The top-level `rabbitmq` key is reserved for consumers. Do not use it to hold named connection
sections for `IRabbitConnection["rabbitmq.events"]`: at `listening()` every value under
`rabbitmq` is treated as a consumer, and a dictionary of named sections fails because it has no
`url`. Put named publisher sections under a key of your own, for example
`"queues": {"events": {...}}`, and inject `IRabbitConnection["queues.events"]`. They take the
same keys as the table above.

## `cache`

Read once when the dispatcher is created (`bclib/cache/factory.py`,
`bclib/cache/signal_base_cache_manager.py`). Usage: [README: Cache](../README.md#15-cache).

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `type` | str | absent: caching disabled | Only `"memory"` is supported. Any other value aborts `from_options`. |
| `clean_interval` | int (seconds) | `43200` | Period for removing expired entries. `0` disables it; negative aborts. |
| `reset_interval` | int (seconds) | `86400` | Period for clearing the whole cache. `0` disables it; negative aborts. |
| `signaler` | dict | none | Remote cache clearing. `{"type": "rabbit", "url": ..., "queue": ...}` consumes `{"type": "clear-cache", "keys": [...]}` messages from that queue. It connects during `from_options`; an unreachable broker aborts start-up. |

## `logger`

Two components read this section.

**Console logger** (`ILogger[...]`, `bclib/logger/console_logger.py`). Usage:
[README: Logger](../README.md#14-logger).

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `level` | str | `"INFO"` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. An unknown name falls back to `INFO`. |
| `format` | str | `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` | Python `logging` format string. |
| `use_colors` | bool | `true` | ANSI colours on console output. |
| `async_logging` | bool | `true` | Write through a background queue thread. |
| `queue_size` | int | `-1` (unbounded) | Queue capacity when `async_logging` is on. |

**Schema log service** (`ILogService`, `bclib/log_service/log_service.py`). This service is
built only when something injects `ILogService`. If you do, `logger` must contain `type`, or
resolution fails:

| Key | Type | Meaning |
|-----|------|---------|
| `type` | str | `"schema.restful"` or `"schema.rabbit"` (case-insensitive). |
| `url` / `get_url` | str | Schema definition endpoint. `url` takes precedence. |
| `url` / `post_url` | str | `schema.restful` only: where log records are POSTed. |
| `connection` | dict | `schema.rabbit` only: `url` plus `queue` or `exchange`, and optional `durable`, `passive`, `exclusive`, `auto_delete`. |

Without a `logger` section, `ILogService` resolves to a no-op service.

## `settings` (legacy `DbManager`)

`IDbManager` (`bclib/db_manager/db_manager.py`) reads entries of `settings` whose key starts
with `connections.`:

```json
"settings": {
  "connections.sqlite.local": "./data/app.db",
  "connections.mongo.archive": "mongodb://localhost:27017"
}
```

The key is `connections.<type>.<name>`. `<type>` is `sql` (ODBC connection string, needs
`pyodbc`), `sqlite` (file path), `mongo` (connection string) or `rest` (base URL). `<name>` is
stored lowercased, so call `open_connection("local")` with the lowercase name. New code should
use the connection interfaces instead ([README: Connections](../README.md#13-connections)).

## Connection sections

These sections have no fixed top-level name; the key you pass as the generic argument selects
them.

**`IMongoConnection["<key>"]`** (`bclib/connections/mongo/mongo_connection.py`):

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `connection_string` | str | required | MongoDB URI. |
| `database_name` | str | required on first use | Database returned by `.database`. |
| `timeout` | int (ms) | driver default | Passed as `connectTimeoutMS`. |
| `server_selection_timeout` | int (ms) | driver default | Passed as `serverSelectionTimeoutMS`. |
| `max_pool_size` / `min_pool_size` | int | driver default | Connection pool bounds. |

**`IRestfulConnection["<key>"]`** (`bclib/connections/restful/restful_connection.py`):

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `base_url` | str | required | Prefix for every request. |
| `timeout` | int (seconds) | `30` | Request timeout. |
| `headers` | dict | `{}` | Headers sent with every request. |
| `ssl_verify` | bool | `true` | `false` disables certificate verification. |
| `ssl_cert_path` | str | none | CA bundle used instead of `certifi`. |

**`IRabbitConnection["<key>"]`**: the same keys as [`rabbitmq` entries](#rabbitmq-entries).

## Keys that 4.0 does not read

These keys still appear in older samples and are silently ignored by 4.0:

| Key | What to do instead |
|-----|--------------------|
| `router` (string or dict) | Nothing. The router is built from the registered handlers. |
| top-level `ssl` | Put `ssl` inside the `http` entry it belongs to. |
| `configuration` | Use `config` inside an `http` entry. |
| `server`, `endpoint` (top-level) | Use `http` or `tcp`. |
| `named_pipe`, `sender`, `receiver`, `defaultRouter` | No equivalent in 4.0. |
| `log_error` | Read, but has no effect. Unhandled exceptions are always logged at `ERROR` with a traceback (`bclib/dispatcher/dispatcher.py`). For tracebacks in responses, use `error_log`. |

## Complete `host.json`

Every framework section, plus three sections of your own (`database`, `services`, and the
legacy `settings`):

```json
{
  "name": "orders-edge",
  "http": [
    "localhost:8080",
    {
      "endpoint": "0.0.0.0:8443",
      "ssl": {
        "certfile": "./certs/server.pem",
        "keyfile": "./certs/server.key"
      },
      "config": {
        "client_max_size": 2097152
      }
    }
  ],
  "tcp": "127.0.0.1:1564",
  "rabbitmq": [
    {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "edge-tasks",
      "durable": true,
      "retry_delay": 10
    }
  ],
  "log_request": true,
  "error_log": false,
  "cache": {
    "type": "memory",
    "clean_interval": 600,
    "reset_interval": 3600
  },
  "logger": {
    "level": "INFO",
    "use_colors": false,
    "async_logging": true
  },
  "settings": {
    "connections.sqlite.local": "./data/app.db"
  },
  "database": {
    "users": {
      "connection_string": "mongodb://localhost:27017",
      "database_name": "users_db",
      "timeout": 5000
    }
  },
  "services": {
    "catalog": {
      "base_url": "https://api.example.com",
      "timeout": 30,
      "headers": { "X-App": "edge" },
      "ssl_verify": true
    }
  }
}
```

To check a file without opening any port, load it and build its listeners without starting
them:

```python
import json
from pathlib import Path

from bclib import edge
from bclib.listener.listener_factory import IListenerFactory
from bclib.options import IOptions

options = json.loads(Path("host.json").read_text(encoding="utf-8"))
app = edge.from_options(options)

sp = app.service_provider
listeners = sp.get_service(IListenerFactory).load_listeners()
print("listeners:", [type(l).__name__ for l in listeners])
print("cache manager:", type(app.cache_manager).__name__)
print("users section:", dict(sp.get_service(IOptions["database.users"])))
```

Output for the file above:

```
listeners: ['HttpListener', 'HttpListener', 'TcpListener', 'RabbitListener']
cache manager: InMemoryCacheManager
users section: {'connection_string': 'mongodb://localhost:27017', 'database_name': 'users_db', 'timeout': 5000}
```

This check does not open certificate files or connect to brokers and databases. Those happen
at `listening()` or on first use.

## Reading configuration errors

When a framework class rejects a value in its constructor (an unknown cache `type`, a missing
`url` in a `rabbitmq` entry), the error that reaches you can be a `TypeError` of the form
`X.__init__() missing N required positional arguments`. The dependency-injection container
retries the constructor without arguments and reports that second failure, not the first.
Treat this message as "the configuration for X is invalid" and check that section against the
tables above.

See also: [architecture.md](architecture.md), [deployment.md](deployment.md),
[limitations.md](limitations.md).
