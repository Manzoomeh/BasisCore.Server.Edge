# BasisEdge developer guide

In-depth documentation for BasisEdge 4.1.0 (`bclib`). Start with the repository
[README](../README.md) for installation, a quick start and the API tour; use these pages when you
need the details behind it.

| Page | Read it for |
|------|-------------|
| [architecture.md](architecture.md) | How a request flows: listeners, message types, context selection, dispatch, responses, errors, DI scopes, start-up and the event loop |
| [basiscore-integration.md](basiscore-integration.md) | Working with the BasisCore web server and BasisCore.js: the TCP frame, the CMS object, response types, client and server source (`dbsource`) |
| [configuration-reference.md](configuration-reference.md) | Every option key 4.1 reads, with types and defaults, a complete `host.json`, and keys that are no longer read |
| [security.md](security.md) | Keeping the TCP endpoint private, TLS, what error responses expose, CORS, static files, request limits, secrets |
| [deployment.md](deployment.md) | Installing, the process model, Docker, OS notes, logging, health checks, graceful shutdown, performance |
| [extending.md](extending.md) | Custom predicates, hosted services, application services through DI, replacing the logger, custom listeners |
| [testing.md](testing.md) | Running the suite, testing handlers without a network, testing over TCP, common pitfalls |
| [limitations.md](limitations.md) | Known gaps in 4.1.0 with work-arounds, and upgrading from 3.x |
| [dependency-injection-multiple-implementations.md](dependency-injection-multiple-implementations.md) | Registering and resolving several implementations of one interface |

Every example on these pages runs against bclib 4.1.0.
