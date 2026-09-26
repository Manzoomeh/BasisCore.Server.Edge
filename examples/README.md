# Examples

Runnable usage samples for **BasisCore.Server.Edge** (`bclib`).

Automated unit tests live in [`tests/`](../tests/). This folder is for learning and copy-paste starters — not CI.

All samples below are intended to start without external brokers/databases (no RabbitMQ, SQL Server, or live BasisCore required).

## Quick start

```bash
# from repo root
pip install -r requirements.txt
# or: set PYTHONPATH to the repo root
python examples/restful/hello.py
```

Servers print a URL then call `app.listening()`. Stop with `Ctrl+C`.

Latest smoke-run logs (one start each): [`_run_outputs/`](_run_outputs/).

## Catalog

| Path | Port | Notes |
|------|------|-------|
| `restful/hello.py` | 9130 | Minimal REST |
| `restful/async_initializers.py` | 9131 | Preload data then listen |
| `restful/simple.py` | 9132 | REST + `@app.cache()` |
| `restful/large_body.py` | 9133 | Large POST body limit |
| `http/simple.py` | 9110 | Web + callback predicate |
| `http/https_pem.py` | 9111 | HTTPS PEM (`http/certs/`) |
| `http/https_pfx.py` | 9112 | HTTPS PFX |
| `predicates/callback.py` | 9120 | `app.callback` |
| `predicates/decorator_parameters.py` | 9121 | Decorator route/method helpers |
| `di/simple_di.py` | 9101 | Singleton DI |
| `di/factory_with_dependencies.py` | 9102 | Factory registration |
| `di/optional_context.py` | 9103 | Handler without context param |
| `di/auto_router.py` | 9104 | Simple REST routes |
| `exceptions/*` | 9140–9146 | HTTP short-circuit errors |
| `logger/di_logger.py` | 9150 | `ILogger` injection |
| `logger/custom_logger.py` | 9151 | Custom `ILogger` impl |
| `logger/no_log.py` | 9152 | `log_request=False` |
| `cache/simple.py` | 9160 | Cache manager API |
| `cache/cache_method.py` | 9161 | `@app.cache` on handler |
| `client_source/simple.py` | 9170 | Client dbsource handlers |
| `server_source/simple.py` | 9171 | Server dbsource handlers |
| `static_file/server.py` | 9180 | `StaticFileHandler` |
| `docker/main.py` | 9181 | Container sample app |
| `web/simple.py` | 9182 | HTML web handlers |
| `streaming/chunk_encoding/simple_stream.py` | 9183 | Chunked web stream |
| `streaming/rest_stream.py` | 9184 | REST stream |
| `websocket/simple.py` | 9185 | WS echo |
| `websocket/chat/server.py` | 9186 | WS group chat |
| `multi_server/simple_rest_a.py` | 9187 | Child A |
| `multi_server/simple_rest_b.py` | 9188 | Child B |
| `multi_server/multi_server.py` | — | `edge.from_list` launcher |
| `parser/answer/*.py` | — | Offline answer-parser scripts |

## Conventions

- Prefer `from bclib import edge`
- Unique localhost ports so samples can run side-by-side
- Keep samples self-contained and runnable from the repo root
- Do not put unit/assert-style scripts here — use `tests/`
