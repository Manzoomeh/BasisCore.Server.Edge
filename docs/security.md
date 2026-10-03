# Security

What BasisEdge 4.1 does, and does not do, at each point where security matters, with the
configuration or code that closes each gap. Key names are defined in
[configuration-reference.md](configuration-reference.md).

## Recommended topology

```
browser ──HTTPS──> BasisCore web server ──TCP (private)──> Edge (tcp listener)
```

The BasisCore web server terminates TLS, routes by domain and URL, and forwards each request to
Edge as a CMS object over the binary TCP protocol. Edge does not check the sender. It uses the
URL, headers, cookies and client IP exactly as the web server reports them. The protocol and
the web server's connection settings are described in
[basiscore-integration.md](basiscore-integration.md). For process layout, see
[deployment.md](deployment.md).

Run the `http` listener on a public interface only when Edge serves clients directly, and then
configure TLS on it as described below.

## Keep the TCP endpoint private

The `tcp` listener (`bclib/listener/tcp/tcp_listener.py`, `bclib/listener/tcp/tcp_message.py`)
has:

- no TLS and no authentication: any peer that can connect is treated as the web server;
- no read timeout: a connection that sends nothing stays open;
- no frame size limit: the 4-byte length fields are trusted, so a peer can make Edge buffer a
  very large frame in memory.

Because the peer supplies the whole request, it can set any value, including
`context.cms["request"]["clientip"]`. Do not base access decisions on the client IP or on
headers unless only the web server can reach the port.

Bind it to loopback when the web server runs on the same host. Otherwise bind it to a private
interface and allow only the web server's address at the firewall:

```json
{ "tcp": "127.0.0.1:1564" }
```

Never use `"0.0.0.0:<port>"` for `tcp` on a host with a public interface.

## TLS on HTTP listeners

TLS is configured per `http` entry, never at the top level:

```python
from bclib import edge
from bclib.context import RESTfulContext

app = edge.from_options({
    "name": "secure-edge",
    "http": {
        "endpoint": "0.0.0.0:8443",
        "ssl": {
            "certfile": "./certs/server.pem",
            "keyfile": "./certs/server.key"
        },
        "config": {
            "client_max_size": 262144,
            "handler_args": {"max_field_size": 8190}
        }
    },
    "error_log": False
})

@app.restful_handler("api/ping")
def ping(context: RESTfulContext):
    return {"ok": True}

if __name__ == "__main__":
    app.listening()
```

What the code does (`bclib/listener/http/http_listener.py`):

- It builds the context with `ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)`. With
  Python 3.13 this means TLS 1.2 or newer, Python's default ciphers, and no client-certificate
  verification. None of these can be changed from options.
- With `pfxfile` and `password`, the bundle is decrypted, and the certificate chain and the
  **unencrypted private key** are written to two temporary files. Both are loaded, then
  deleted. Keep the system temp directory private to the service account.
- Certificate files are loaded when `listening()` starts the listener, not in `from_options`.

What happens when the configuration is wrong:

| Problem | Result |
|---------|--------|
| `certfile`, `keyfile` or `pfxfile` path does not exist | `FileNotFoundError`, reported as `Task exception was never retrieved` |
| `certfile` without `keyfile`, or `pfxfile` without `password` | `KeyError: 'keyfile'` / `KeyError: 'password'`, reported the same way |
| Wrong PKCS#12 password | `ValueError: Invalid password or PKCS12 data`, reported the same way |
| `ssl` present but has neither `certfile` nor `pfxfile` (for example `cert` / `key`) | The listener starts and logs `https://...`, but every TLS handshake is reset |

In the first three cases **the process keeps running**, and other listeners keep working.
Only that HTTP port is never opened. After a deployment, confirm that the log contains
`Development Edge server started at https://<host>:<port>` for every TLS listener, and that
the port accepts a handshake.

## What error responses expose

When a handler raises, the dispatcher logs the exception at `ERROR` with its traceback
(`bclib/dispatcher/dispatcher.py`, `dispatch_async`; an unmatched request is one `WARNING`
line), then asks the context to build the response (`bclib/context/cms_base_context.py`,
`_generate_error_object`):

- **Every** error response contains `str(exception)` as `errorMessage`, whatever the options.
  An exception from a database driver can carry a host name, a user name or a query.
- With `"error_log": true`, the full Python traceback is added: as an `error` field in JSON
  (`RESTfulContext`), or after an `<hr/>` in HTML (`HttpContext`). The traceback includes file
  paths and source lines. Use it only in development.
- HTML error pages HTML-escape the message, the error code and the traceback, so request input
  echoed in an exception cannot inject markup. `ShortCircuitErr.data` is inserted as given, so
  never put request input into it unescaped.
- For a `ShortCircuitErr` subclass that carries `data`, the response is that `data`, with no
  traceback.
- When a request fails before a context exists, the reply is an escaped HTML page of the form
  `Edge could not process the request: <Type>: <message>`, with the exception's status for a
  `ShortCircuitErr` and `500` otherwise.

Keep `error_log` off in production. Raise framework errors with fixed, user-safe messages, and
convert everything else:

```python
import logging

from bclib import edge
from bclib.context import RESTfulContext
from bclib.exception import BadRequestErr, InternalServerErr, ShortCircuitErr

app = edge.from_options({"http": "localhost:8080", "error_log": False})
log = logging.getLogger("orders")

def load_order(order_id: int) -> dict:
    raise ConnectionError("mongodb://admin:pw@db.internal:27017 unreachable")

@app.restful_handler("api/orders/:order_id")
def get_order(context: RESTfulContext):
    order_id = context.url_segments.get("order_id", "")
    if not order_id.isdigit():
        raise BadRequestErr("order id must be numeric")
    try:
        return load_order(int(order_id))
    except ShortCircuitErr:
        raise
    except Exception:
        log.exception("loading order failed")
        raise InternalServerErr("internal error")
```

Responses: `/api/orders/abc` returns `400 {"errorCode": "http-400", "errorMessage": "order id must be numeric"}`,
and `/api/orders/12` returns `500 {"errorCode": "http-500", "errorMessage": "internal error"}`.
The connection string appears only in the server log. Error types and codes:
[README: Errors & Status Codes](../README.md#16-errors--status-codes).

## CORS

There is no built-in CORS policy. Edge adds no `Access-Control-*` header on its own, and it
does not answer preflight requests. An `OPTIONS` request is routed like any other method:
a handler registered without `method=` answers it with its normal body.

`HttpHeaders.add_cors_headers(context)` (`bclib/utility/http_headers.py`) adds
`Access-Control-Allow-Origin: *` and a fixed `Access-Control-Allow-Headers` list. Use it only
for public, credential-free data. For anything else, allow named origins explicitly:

```python
from bclib import edge
from bclib.context import RESTfulContext
from bclib.utility import HttpHeaders

ALLOWED_ORIGINS = {"https://app.example.com"}

app = edge.from_options({"http": "localhost:8080"})

def apply_cors(context: RESTfulContext) -> None:
    origin = context.cms.get("request", {}).get("origin")
    if origin in ALLOWED_ORIGINS:
        context.add_header(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, origin)
        context.add_header("Vary", "Origin")

@app.restful_handler("api/items", method="OPTIONS")
def preflight(context: RESTfulContext):
    apply_cors(context)
    context.add_header(HttpHeaders.ACCESS_CONTROL_ALLOW_METHODS, "GET, POST")
    context.add_header(HttpHeaders.ACCESS_CONTROL_ALLOW_HEADERS, "Content-Type, Authorization")
    return {}

@app.restful_handler("api/items", method="GET")
def list_items(context: RESTfulContext):
    apply_cors(context)
    return {"items": []}
```

Request headers arrive lowercased under `context.cms["request"]`. Behind the BasisCore web
server, you can apply the same policy in the web server instead.

WebSocket upgrades are accepted without an `Origin` check
(`bclib/listener/http/websocket_session_manager.py`). If a WebSocket handler relies on
cookies, check the `origin` value in the request data before acting on messages.

## Static files

`StaticFileHandler` (`bclib/utility/static_file_handler.py`; usage in
[README: Static Files](../README.md#17-static-files)) does this:

| Check | Behaviour today |
|-------|-----------------|
| Path traversal | The target is resolved, symlinks included, and must stay inside `base_dir`; otherwise `403`. Encoded `..%2F` is caught too. |
| Hidden files | A path with any segment starting with `.` (`.env`, `.git/config`) is not served and falls through to your handlers, or to a `404`. Pass `allow_hidden=True` to serve them. |
| Extension whitelist | Optional. Without `allowed_extensions`, every other file under `base_dir` is served. |
| HTTP method | Only GET and HEAD are served; other methods fall through to your handlers, or to a `404`. |
| `url_prefix` | Stripped when the path starts with it as a whole segment (`static/app.js`, not `staticx/app.js`); `"static"` and `"/static"` are the same. Never required: the same files are also served without the prefix. |
| Error pages | Message and traceback are HTML-escaped. |
| Directory index | Only the names in `index_files`; directory listing is never produced. |
| Large files | Read fully into memory before sending. |

Always pass `allowed_extensions`, keep only public files under `base_dir`, and keep secrets and
source code outside it:

```python
from pathlib import Path

from bclib import edge
from bclib.utility import StaticFileHandler

app = edge.from_options({"http": "localhost:8080"})

app.add_static_handler(StaticFileHandler(
    base_dir=str(Path(__file__).parent / "public"),
    allowed_extensions={".html", ".css", ".js", ".png", ".svg"},
    enable_index=True,
    url_prefix="static",
))
```

With this handler, `/static/app.js` and `/app.js` return the file, `/static/.env` and a `POST`
to `/static/app.js` return 404, and `/static/..%2F..%2Fapp.py` returns 403.

## Request size and timeouts

| Limit | Where | Default | Configurable |
|-------|-------|---------|--------------|
| Request body, multipart included | `http` entry, `config.client_max_size` | 1 MiB, `413` beyond | yes |
| Header line length, keep-alive | `http` entry, `config.handler_args` (aiohttp keys such as `max_field_size`, `keepalive_timeout`) | aiohttp defaults | yes |
| Handler execution time | none | unlimited | no; apply `asyncio.wait_for` in your own code |
| TCP frame size and read time | none | unlimited | no; keep the port private |
| Outgoing REST calls | connection section `timeout` | 30 s | yes |

Raise `client_max_size` only on listeners that need large uploads, because an accepted upload
is held in memory as a whole.

## Secrets in configuration

`host.json` values are used literally. There is no `${VAR}` expansion and no environment
lookup anywhere in the options code. Because `from_options` takes a plain dictionary, read
secrets from the environment (or a secret store) in Python and merge them in before the call:

```python
import json
import os

from bclib import edge

with open("host.json", encoding="utf-8") as f:
    options = json.load(f)

options["database"]["users"]["connection_string"] = os.environ["USERS_MONGO_URI"]
options["http"]["ssl"]["password"] = os.environ["EDGE_PFX_PASSWORD"]

app = edge.from_options(options)
```

Also:

- With `log_request` on (the default), every request URL, **query string included**, is written
  to the log. Do not pass tokens in query strings.
- Any handler can inject `AppOptions` and read every secret in the options. Treat the whole
  options dictionary as sensitive.
- `"ssl_verify": false` on a REST connection section disables certificate checks for that
  upstream. Use `ssl_cert_path` for a private CA instead.

## Checklist

- [ ] `tcp` is bound to loopback or a private interface, and firewalled to the web server.
- [ ] Every public `http` listener has `ssl`, and its `https://` start-up line appears in the log.
- [ ] `error_log` is `false`; handlers raise fixed messages and never echo input into exceptions.
- [ ] CORS headers are set explicitly for named origins, or by the web server.
- [ ] Every `StaticFileHandler` has `allowed_extensions`, and `base_dir` holds only public files.
- [ ] `client_max_size` is set per listener to what that listener needs.
- [ ] Secrets come from the environment, not from `host.json` in version control.

Known gaps are also tracked in [limitations.md](limitations.md). To test these behaviours in
your own app, see [testing.md](testing.md).
