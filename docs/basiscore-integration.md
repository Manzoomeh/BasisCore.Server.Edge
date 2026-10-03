# Working with BasisCore

BasisEdge speaks the BasisCore request model natively: every request is a **CMS object**, every
reply is the same object with a `cms` node added, and `dbsource` commands from BasisCore pages map
to source and member handlers. This page describes those contracts as implemented in 4.1. For the
general request pipeline see [architecture.md](architecture.md); for handler basics see
[README §8](../README.md#8-handlers) and [README §20](../README.md#20-client--server-source-dbsource).

There are two ways BasisCore traffic reaches Edge:

| Caller | Transport | What arrives | Typical handlers |
|--------|-----------|--------------|------------------|
| BasisCore web server | TCP listener, binary frame | a CMS object prepared by the web server | `web_handler`, `restful_handler`, `server_source_handler` |
| Browser (BasisCore.js, other clients) | HTTP listener | an HTTP request, converted to a CMS object by Edge | `web_handler`, `restful_handler`, `client_source_handler` |

In both cases the CMS object is routed and dispatched the same way.

## The TCP frame

The `tcp` option starts a `TcpListener` (see [README §18.6](../README.md#186-tcp)). It reads exactly
one frame per connection, dispatches it, writes one reply frame and closes the connection.

All integers are 4-byte big-endian; strings are UTF-8.

| Field | Size | Notes |
|-------|------|-------|
| message type | 1 byte | `MessageType` value: `1` CONNECT, `2` MESSAGE, `3` DISCONNECT, `4` AD_HOC, `5` NOT_EXIST |
| session id length | 4 bytes | |
| session id | n bytes | echoed back in the reply |
| payload length | 4 bytes | only for types 1, 2 and 4 |
| payload | n bytes | a JSON document `{"cms": {...}}` |

Notes:

- Requests use type `4` (AD_HOC). Frames of type `3` or `5` have no payload and are not dispatched.
- The reply has the same type and session id as the request. Its payload is the response CMS
  object as JSON (see [The response](#the-response)).
- A payload that is not valid JSON or UTF-8 is treated as an empty object, which fails routing and
  produces a `500` reply (see [architecture.md](architecture.md#errors)).
- Because the reply is JSON, a handler must not return `bytes` to a TCP caller: the reply cannot be
  encoded and the caller receives a `500` CMS reply instead.

A minimal client, useful for testing an Edge service without the web server:

```python
import asyncio
import json
import struct

from bclib import edge
from bclib.context import HttpContext

app = edge.from_options({"name": "tcp-demo", "tcp": "127.0.0.1:3010", "log_request": False})


@app.web_handler("hello")
def hello(context: HttpContext):
    return f"Hello {context.query.get('name', 'world')}"


async def send_frame(host: str, port: int, session_id: str, cms: dict) -> dict:
    reader, writer = await asyncio.open_connection(host, port)
    sid = session_id.encode("utf-8")
    payload = json.dumps(cms).encode("utf-8")
    # type (AD_HOC = 4), session id length + bytes, payload length + bytes; big-endian
    writer.write(struct.pack(">BI", 4, len(sid)) + sid + struct.pack(">I", len(payload)) + payload)
    await writer.drain()
    msg_type, sid_len = struct.unpack(">BI", await reader.readexactly(5))
    reply_sid = (await reader.readexactly(sid_len)).decode("utf-8")
    (length,) = struct.unpack(">I", await reader.readexactly(4))
    reply = json.loads(await reader.readexactly(length))
    writer.close()
    print("type:", msg_type, "session:", reply_sid)
    return reply


async def main():
    await app.initialize_task_async()
    await asyncio.sleep(0.2)  # the listener starts in a background task
    request = {"cms": {
        "request": {"full-url": "www.example.com/hello?name=Ada", "url": "hello",
                    "methode": "get", "request-id": "17"},
        "query": {"name": "Ada"},
    }}
    reply = await send_frame("127.0.0.1", 3010, "session-1", request)
    print(json.dumps(reply, indent=2))

loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
loop.run_until_complete(main())
```

Output:

```text
type: 4 session: session-1
{
  "request": {
    "full-url": "www.example.com/hello?name=Ada",
    "url": "hello",
    "methode": "get",
    "request-id": "17"
  },
  "query": {
    "name": "Ada"
  },
  "cms": {
    "webserver": {
      "index": "5",
      "headercode": "200 OK",
      "mime": "text/html"
    },
    "content": "Hello Ada"
  }
}
```

Note the shape: the request payload wraps everything in `cms`, while the reply is the *contents*
of that node with a new `cms` node holding the response.

## The CMS object

### Request

The payload's `cms` node has these sections. Over TCP the caller provides them; over HTTP,
`WebRequestHelper` builds them from the aiohttp request.

| Section | Contents |
|---------|----------|
| `request` | request metadata and headers (below) |
| `query` | query-string values; a repeated key becomes a list |
| `form` | URL-encoded or multipart form fields |
| `cookie` | cookies, one key per cookie |
| `cms` | server values: `date` (`dd/mm/yyyy`), `time` (`HH:MM`), `date2` (`yyyymmdd`), `time2` (`HHMMSS`), `date3` (`yyyy.mm.dd`) |
| `files` | multipart uploads: `field`, `name`, `size`, `content_type`, `content` |

Keys in `request`:

| Key | Meaning | Used by Edge for |
|-----|---------|------------------|
| `full-url` | host and path with query, without scheme, e.g. `www.example.com:8080/api/users?id=1` | **required**; context selection |
| `url` | path without leading `/` and without query, e.g. `api/users` | `Url` predicates, `context.url` |
| `methode` | lower-case HTTP method (the key is spelled `methode`) | `method=` and `app.get()`-style predicates, `context.methode` |
| `rawurl` | path and query without leading `/` | |
| `request-id` | request number (a per-process counter for HTTP) | request log line |
| `host`, `port` | from the `Host` header | |
| `hostip`, `hostport`, `clientip` | server and client addresses | |
| `content-type`, `body` | body as text (base64 if it is not UTF-8) | `RESTfulContext.body` |
| other headers | lower-cased header name → value | |

A CMS object without `request`, or a `request` without `full-url`, is rejected before a context
is created and answered with a `500` reply.

Contexts expose the common parts directly: `context.cms` (the whole object), `context.url`,
`context.query`, `context.form`, `context.methode`, and, on `RESTfulContext`, `context.body`
(the form, or the parsed JSON or URL-encoded body). See [README §9](../README.md#9-contexts).

### The response

`generate_response` adds (or extends) the `cms` node of the request object:

```json
{
  "request": {"...": "..."},
  "cms": {
    "webserver": {"index": "1", "headercode": "200 OK", "mime": "text/html"},
    "content": "<basis core=\"print\" name=\"p42\"></basis>",
    "http": {"Cache-Control": "no-store"}
  }
}
```

| Key | Set from | Default |
|-----|----------|---------|
| `cms.webserver.index` | `context.response_type` | `ResponseTypes.RENDERED` (`"5"`) |
| `cms.webserver.headercode` | `context.status_code` | `"200 OK"` (`HttpStatusCodes.OK`) |
| `cms.webserver.mime` | `context.mime` | `text/html`; `application/json` for `RESTfulContext` and `ClientSourceContext` |
| `cms.content` | a `str` result, or any other non-bytes result as JSON | |
| `cms.blob-content` | a `bytes` result | |
| `cms.http` | `context.add_header(name, value)`; repeated values are joined with `,` | |

`index` tells the web server what to do with the reply. The values are the string constants in
`bclib.utility.ResponseTypes`:

| Constant | Value | Meaning |
|----------|-------|---------|
| `RENDERABLE` | `"1"` | content contains BasisCore markup for the web server to render |
| `STATIC_FILE` | `"2"` | send the file at `cms.webserver.filepath` |
| `PROXY` | `"3"` | proxy response |
| `STATIC_FILE_WITH_PROCESS` | `"4"` | static file with processing |
| `RENDERED` | `"5"` | final content, send as is |

Edge's own HTTP listener acts on `"2"` (it streams the file from `filepath`, see
[README §17](../README.md#17-static-files)); for every other value it sends `content` or
`blob-content` with the given status, MIME type and headers. The distinction between `"1"` and
`"5"` matters when the reply goes to the BasisCore web server over TCP.

A page handler that hands BasisCore markup back for rendering:

```python
from bclib.context import HttpContext
from bclib.utility import ResponseTypes


@app.web_handler("product/:id")
def product_page(context: HttpContext, id: str):
    context.response_type = ResponseTypes.RENDERABLE
    context.add_header("Cache-Control", "no-store")
    return f'<basis core="print" name="p{id}"></basis>'
```

For `product/42` this produced the `cms` node shown above.

## dbsource commands: client source and server source

A `<basis core="dbsource">` command names a data source and lists the result sets it expects as
`<member>` children. Edge answers such a command with two levels of handlers:

1. a **source handler** runs once per command and returns the data;
2. for every `<member>`, in document order, a **member handler** is dispatched with that data and
   returns the rows for that member.

| | Client source | Server source |
|-|---------------|---------------|
| Source decorator / context | `client_source_handler` / `ClientSourceContext` | `server_source_handler` / `ServerSourceContext` |
| Member decorator / context | `client_source_member_handler` / `ClientSourceMemberContext` | `server_source_member_handler` / `ServerSourceMemberContext` |
| Where the command comes from | form field `command` (`cms.form.command`) | `cms.command` in the TCP payload |
| Domain id (`context.dmn_id`) | form field `dmnid` | `cms.dmnid` |
| Parameters (`context.params`) | `<params><add name=".." value=".."></add></params>` inside the command, as a dict | `cms.params` |
| Transport | HTTP or TCP | TCP only |
| Reply | envelope as JSON in `cms.content` (`application/json`) | the envelope itself, not wrapped in a CMS object |
| URL routes on the source handler | supported | not supported: a `Url` predicate never matches a `ServerSourceContext`; register without a route and select with predicates such as `app.equal("context.command.name", "report")` |

How a page's command reaches a handler:

- **Client-side** (`run="atclient"`): Edge expects a form post to a URL it routes, carrying the
  command markup in the field `command` and the domain id in `dmnid`. Point the source's connection
  at that URL, for example `https://www.example.com/source`, and register
  `@app.client_source_handler("source")`.
- **Server-side**: Edge expects a TCP frame whose `cms` node holds `request` (with `full-url`,
  needed for routing) together with `command`, `dmnid` and `params`.

The command is parsed with an HTML parser into `context.command`, a `DictEx`: attributes become
lower-case keys (`context.command.name`, `context.command.source`, `context.command.mid`) and child
elements become lists (`context.command.member`, `context.command.params`). The original markup is
in `context.raw_command`.

### The envelope

Both source decorators build the same envelope from the member results:

```json
{
  "setting": {"keepalive": false},
  "sources": [
    {
      "options": {
        "tableName": "<command name>.<member name>",
        "keyFieldName": null,
        "statusFieldName": null,
        "mergeType": 0,
        "columnNames": null
      },
      "data": "<member handler result>"
    }
  ]
}
```

- One `sources` entry per `<member>`, in the order they appear in the command.
- `tableName` is always `"{command.name}.{member.name}"`.
- `keyFieldName`, `statusFieldName`, `mergeType` and `columnNames` come from the member context
  attributes `key_field_name`, `status_field_name`, `merge_type` and `column_names`, which a member
  handler may set.
- `mergeType` is the numeric value of `bclib.context.MergeType`: `REPLACE` = `0` (default),
  `APPEND` = `1`.
- If the source handler returns `None`, the command is treated as not handled and the next source
  handler is tried.
- If no member handler matches a member, or one raises, that member's `data` is an error object
  such as `{"errorCode": null, "errorMessage": "Suitable handler not found for ClientSourceMemberContext!"}`;
  the other members are unaffected.

Member contexts carry `member` (the `<member>` element's attributes, e.g. `context.member.name`),
`data` (the source handler's result, the same object for every member), `command`, and on the
client side `cms` and `url`. Each member gets its own member context, so the options a handler sets
apply to its member only. Select member handlers with predicates on these attributes; URL routes
do not apply to member contexts.

### Example: a catalog dbsource

The page holds the command shown in `COMMAND` below. The Edge handlers, plus a request built in
code so the example runs without a browser:

```python
import asyncio
import json

from bclib import edge
from bclib.context import (ClientSourceContext, ClientSourceMemberContext,
                           MergeType)
from bclib.listener.http.http_message import HttpMessage

app = edge.from_options({"name": "catalog", "log_request": False})

PRODUCTS = [
    {"id": 1, "title": "Desk", "price": 120},
    {"id": 2, "title": "Chair", "price": 45},
    {"id": 3, "title": "Lamp", "price": 18},
]


@app.client_source_handler("source", app.equal("context.command.name", "catalog"))
def catalog_source(context: ClientSourceContext):
    # Runs once per dbsource command; the return value is shared by every member.
    max_price = int(context.params.get("maxprice", 1000)) if context.params else 1000
    return [p for p in PRODUCTS if p["price"] <= max_price]


@app.client_source_member_handler(app.equal("context.member.name", "items"))
def items_member(context: ClientSourceMemberContext):
    context.key_field_name = "id"
    context.merge_type = MergeType.APPEND
    return context.data


@app.client_source_member_handler(app.equal("context.member.name", "summary"))
def summary_member(context: ClientSourceMemberContext):
    return [{"count": len(context.data)}]


COMMAND = """<basis core="dbsource" run="atclient" name="catalog" source="shop">
  <params><add name="maxprice" value="100"></add></params>
  <member name="items"></member>
  <member name="summary"></member>
</basis>"""

request = {"cms": {
    "request": {"full-url": "localhost:8080/source", "url": "source", "methode": "post"},
    "form": {"command": COMMAND, "dmnid": "1001"},
}}


async def main():
    await app.initialize_task_async()
    message = HttpMessage(request)
    await app.on_message_receive_async(message)
    cms = message.response_data["cms"]
    print(json.dumps(cms["webserver"]))
    print(json.dumps(json.loads(cms["content"]), indent=2))

loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
loop.run_until_complete(main())
```

Output (`cms.webserver`, then the decoded `cms.content`):

```text
{"index": "5", "headercode": "200 OK", "mime": "application/json"}
{
  "setting": {
    "keepalive": false
  },
  "sources": [
    {
      "options": {
        "tableName": "catalog.items",
        "keyFieldName": "id",
        "statusFieldName": null,
        "mergeType": 1,
        "columnNames": null
      },
      "data": [
        {
          "id": 2,
          "title": "Chair",
          "price": 45
        },
        {
          "id": 3,
          "title": "Lamp",
          "price": 18
        }
      ]
    },
    {
      "options": {
        "tableName": "catalog.summary",
        "keyFieldName": null,
        "statusFieldName": null,
        "mergeType": 0,
        "columnNames": null
      },
      "data": [
        {
          "count": 2
        }
      ]
    }
  ]
}
```

In production, remove the `request`/`main` part and call `app.listening()` with an `http` endpoint.

### Server source over TCP

The same pattern on the server side, selected by command name instead of URL:

```python
from bclib.context import ServerSourceContext, ServerSourceMemberContext


@app.server_source_handler(app.equal("context.command.name", "report"))
def report(context: ServerSourceContext):
    return [{"dmnid": context.dmn_id, "x": 1}]


@app.server_source_member_handler()
def member(context: ServerSourceMemberContext):
    return context.data
```

Sent as an AD_HOC frame with session id `s-1` and this payload:

```json
{"cms": {"request": {"full-url": "localhost/report"},
         "command": "<basis core='dbsource' name='report'><member name='rows'></member></basis>",
         "dmnid": "1001"}}
```

the reply frame (type `4`, session `s-1`) carries the bare envelope:

```json
{"setting": {"keepalive": false}, "sources": [{"options": {"tableName": "report.rows", "keyFieldName": null, "statusFieldName": null, "mergeType": 0, "columnNames": null}, "data": [{"dmnid": "1001", "x": 1}]}]}
```

An HTTP request that routing assigns to a server source handler (for example because a
`server_source_handler` registered without a route owns the wildcard) has no `cms.command`. It is
rejected before a context is created and answered with `400 Bad Request` and the message
`server source request has no 'command'; a dbsource sent over HTTP must be handled as a client source`
(HTML-escaped). Browser-side `dbsource` commands belong to `client_source_handler`.

## Related

- [architecture.md](architecture.md): routing, dispatch and error handling.
- [security.md](security.md): validating `dmnid`, `params` and other caller-supplied values.
- [testing.md](testing.md): testing handlers with constructed messages.
- [configuration-reference.md](configuration-reference.md): `http` and `tcp` options.
