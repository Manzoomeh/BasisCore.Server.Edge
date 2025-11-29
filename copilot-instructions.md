# BasisCore.Server.Edge - Project Architecture

BasisCore is an async Python web framework with integrated dependency injection, predicate-based routing, and **multi-protocol listener architecture** (HTTP, WebSocket, Socket, RabbitMQ).

## Core Architecture Overview

```
Edge Layer (edge.py)
  └─ Dispatcher (single unified class)
       ├─ Routing Engine (auto-generated from handlers)
       ├─ Context Detection (pattern-based)
       ├─ DI Container (Singleton/Scoped/Transient)
       ├─ WebSocket Manager (session management)
       └─ Listeners Collection (composition-based)
            ├─ HttpListener (HTTP/HTTPS server)
            ├─ TcpListener (bidirectional TCP)
            ├─ EndpointListener (TCP connections)
            └─ RabbitListener (RabbitMQ)
```

## Architecture Layers

### 1. Edge Layer (`edge.py`)

Factory methods for creating configured Dispatcher instances:

```python
from bclib import edge

# Create from config file
app = edge.from_config(".", "host.json")

# Create from options dict - listeners added automatically
app = edge.from_options({
    "server": "localhost:8080"  # Adds HttpListener
})

# Multiple listeners can coexist
app = edge.from_options({
    "server": "localhost:8080",  # HTTP server
    "receiver": "localhost:8081",
    "sender": "localhost:8082"    # Socket listener
})

# Endpoint configuration
app = edge.from_options({
    "endpoint": "localhost:8080"  # TCP endpoint handler
})
```

### 2. Dispatcher Layer (`bclib/dispatcher/`)

**Unified Dispatcher Architecture** (v3.37.0+):

The framework now uses a **single `Dispatcher` class** with **composition-based listener pattern** instead of inheritance hierarchy.

**Key Classes:**

- `Dispatcher` - Unified dispatcher with routing, DI, and listener management
- `WebSocketSession` / `WebSocketSessionManager` - WebSocket connection management

**Deprecated Classes (backward compatible):**

- `RoutingDispatcher` → `Dispatcher` (alias)
- `DevServerDispatcher` → `Dispatcher` + `HttpListener` (alias)
- `SocketDispatcher` → `Dispatcher` + `TcpListener` (alias)
- `EndpointDispatcher` → `Dispatcher` + `EndpointListener` (alias)

**Dispatcher Features:**

- Auto-router generation from registered handlers
- Dynamic router rebuild on handler changes
- Pattern-based multi-context routing (`:param` syntax → regex)
- Integrated dependency injection container
- WebSocket session management
- Multiple listener support (HTTP + Socket + Rabbit simultaneously)

**Listener Management:**

```python
# Listeners are added via edge.from_options() automatically
# Or manually:
from bclib.listener.http import HttpListener

listener = HttpListener(...)
app.add_listener(listener)
```

**Predicate Helper Methods (in Dispatcher):**

```python
# URL patterns
app.url("api/users/:user_id")

# HTTP methods
app.get("api/users")
app.post("api/users")
app.put("api/users/:id")
app.delete("api/users/:id")
app.options("api/users")

# Method checkers
app.is_get()
app.is_post()

# Other predicates
app.equal(key, value)
app.between(key, min, max)
app.in_list(key, values)
app.match(pattern)
app.has_value(key)
app.all(*predicates)
app.any(*predicates)
app.callback(func)
```

### 3. Context Layer (`bclib/context/`)

Request contexts for different protocols:

**Context Types:**

- `RESTfulContext` - REST API requests (JSON responses)
- `WebContext` - Web page requests (HTML responses)
- `SocketContext` - Raw socket connections
- `WebSocketContext` - WebSocket connections
- `ClientSourceContext` - Client-initiated connections
- `ServerSourceContext` - Server-initiated connections
- `RabbitContext` - RabbitMQ messages

**Base Context (`Context`):**

- `services` property - Scoped ServiceProvider for DI
- `url_segments` - URL path parameters dict
- Database connection helpers:
  - `open_sql_connection(key)` - SQL databases
  - `open_sqlite_connection(key)` - SQLite
  - `open_mongo_connection(key)` - MongoDB
  - `open_restful_connection(key)` - REST APIs
  - `open_rabbit_connection(key)` - RabbitMQ

**RESTfulContext:**

- `to_json()` - Parse request body as JSON
- `check_schema(schema)` - Validate against schema
- `return_value` - Set response dict/list

**WebContext:**

- `return_value` - Set HTML string response

### 4. Listener Layer (`bclib/listener/`)

Protocol-specific listeners using composition pattern:

**Listeners:**

- `HttpListener` (in `http/`) - aiohttp-based HTTP/HTTPS server
- `TcpListener` - Bidirectional raw socket server
- `RabbitListener` / `RabbitBusListener` - RabbitMQ integration
- Endpoint - TCP connection handler (not a separate listener class)

**Messages:**

- `Message` - Base message with session_id, type, buffer
- `WebMessage` - HTTP request/response wrapper
- `TcpMessage` - Socket data wrapper
- `WebSocketMessage` - WebSocket frame wrapper

### 5. Predicate Layer (`bclib/predicate/`)

Request filtering and routing:

**Base Class:** `Predicate`

- Property: `exprossion` (note: typo in codebase, not "expression")
- Method: `async check_async(context: Context) -> bool`

**Common Predicates:**

- `Url` - URL pattern matching with `:param` syntax
- `Equal` - Key-value equality check
- `Between` - Range check
- `InList` - Value in list check
- `Match` - Regex pattern matching
- `All` - Logical AND
- `Callback` - Custom function predicate

**URL Pattern Syntax:**

```python
# :param converts to (?P<param>[^/]+) regex
app.url("api/users/:user_id")           # One parameter
app.url("api/:resource/:id")            # Multiple parameters
app.url("files/:path+")                 # Greedy match (rest of path)
```

### 6. Dependency Injection (`bclib/service_provider/`)

Built-in DI container with three lifetimes:

**Service Lifetimes:**

- **Singleton** - One instance for entire application
- **Scoped** - One instance per request/context
- **Transient** - New instance every time

**Registration:**

```python
# Singleton (application-wide)
app.add_singleton(ILogger, ConsoleLogger)
app.add_singleton(IConfig, instance=config_obj)

# Scoped (per-request)
app.add_scoped(IDatabase, PostgresDatabase)

# Transient (always new)
app.add_transient(IRequestHandler, RequestHandler)
```

**Automatic Injection in Handlers:**

```python
@app.restful_handler(app.url("api/users/:user_id"))
async def get_user(context: RESTfulContext, logger: ILogger, db: IDatabase):
    # Services injected automatically by type hints
    logger.log(f"Getting user {context.url_segments['user_id']}")
    user = await db.get_user_async(context.url_segments['user_id'])
    return {"user": user}
```

**Injection Rules:**

- First parameter must be Context (or omitted for background tasks)
- Additional parameters injected by **type annotation**, not name
- Services resolved from scoped provider (context.services)
- Constructor injection supported in service classes

## Handler Registration System

### Decorator Methods

All decorators are defined in `Dispatcher` class:

```python
# RESTful API handlers (return dict/list → JSON)
@app.restful_handler(predicate1, predicate2, ...)
async def handler(context: RESTfulContext, service1: IService1, ...):
    return {"data": "response"}

# Web page handlers (return str → HTML)
@app.web_handler(predicate1, predicate2, ...)
async def handler(context: WebContext, service1: IService1, ...):
    return "<html>...</html>"

# Socket handlers
@app.socket_action(predicate1, predicate2, ...)
async def handler(context: SocketContext, service1: IService1, ...):
    # Handle socket data
    pass

# WebSocket handlers
@app.websocket_handler(predicate1, predicate2, ...)
async def handler(context: WebSocketContext, service1: IService1, ...):
    # Handle WebSocket messages
    pass

# RabbitMQ handlers
@app.rabbit_handler(predicate1, predicate2, ...)
async def handler(context: RabbitContext, service1: IService1, ...):
    # Handle RabbitMQ messages
    pass

# Background tasks (run on startup)
@app.background_task()
async def task(service1: IService1, ...):
    # No context parameter
    while True:
        await asyncio.sleep(60)
        # Do periodic work
```

### Handler Requirements

1. **Must be async functions**
2. **First parameter** must be appropriate Context type (except background tasks)
3. **Additional parameters** are auto-injected services (by type hints)
4. **Return types:**
   - `RESTfulContext`: dict/list → JSON response
   - `WebContext`: str → HTML response
   - Socket/WebSocket: any → custom handling
   - Background tasks: No return value expected

### Predicate Helper Examples

```python
# URL patterns (converted to regex internally)
app.url("api/users")              # Exact match
app.url("api/users/:user_id")     # Path parameter
app.url("api/:resource/:id")      # Multiple parameters
app.url("files/:path+")           # Greedy (rest of path)

# HTTP method predicates
app.get("api/users")              # GET + URL
app.post("api/users")             # POST + URL
app.put("api/users/:id")          # PUT + URL
app.delete("api/users/:id")       # DELETE + URL

# Method checkers (no URL)
app.is_get()
app.is_post()

# Other predicates
app.equal("header.content-type", "application/json")
app.between("query.page", 1, 100)
app.in_list("query.status", ["active", "pending"])
app.has_value("body.username")

# Logical operators
app.all(app.is_post(), app.url("api/login"))
app.any(app.url("api/v1/users"), app.url("api/v2/users"))
```

## Routing System

### Auto-Generated Router

Router is automatically built from registered handlers:

1. **Single context type** → Simple context detection
2. **Multiple context types** → Pattern-based routing:
   - Extract URL patterns from `Url` predicates
   - Convert BasisCore patterns to regex: `:param` → `(?P<param>[^/]+)`
   - Match incoming URLs against patterns to determine context type
3. **Rebuilds automatically** when handlers are registered/unregistered (unless manually configured)

### Router Lifecycle

```python
# Router initialization happens in initialize_task() before listeners start
# Call __ensure_router_initialized() manually if needed:
app.ensure_router_ready()  # Public method for explicit initialization
```

### Manual Router Configuration

```python
options = {
    "server": "localhost:8080",
    "router": "restful"  # Explicit router type prevents auto-generation
}
```

### Multi-Context Pattern Detection

When handlers for different contexts (RESTful, Web) are registered:

1. Framework extracts URL patterns from `Url` predicates in handler decorators
2. Converts BasisCore `:param` syntax to regex: `(?P<param>[^/]+)`
3. Incoming URLs matched against patterns to determine context type
4. Appropriate context created and handler dispatched

**Example:**

```python
# RESTful handlers
@app.restful_handler(app.url("api/users"))
async def api_handler(context: RESTfulContext):
    return {"users": []}

# Web handlers
@app.web_handler(app.url("index.html"))
async def web_handler(context: WebContext):
    return "<html><body>Home</body></html>"

# Framework auto-detects:
# /api/users → RESTfulContext
# /index.html → WebContext
```

## Code Style Guidelines

### General Rules

- **Always use async/await** - Framework is fully asynchronous
- **Type hints required** - Used for automatic DI injection
- **snake_case** for functions/methods/variables
- **PascalCase** for classes
- **Avoid blocking operations** - Use async libraries only (aiohttp, asyncpg, motor, etc.)

### Handler Guidelines

```python
# ✅ GOOD - Type hints for auto-injection
@app.restful_handler(app.url("api/data"))
async def get_data(context: RESTfulContext, logger: ILogger, db: IDatabase):
    logger.log("Request received")
    data = await db.fetch_async()
    return {"data": data}

# ❌ BAD - No type hints, manual service resolution
@app.restful_handler(app.url("api/data"))
async def get_data(context):
    logger = context.services.get_service("logger")  # Don't do this!
    return {"data": "value"}

# ✅ GOOD - Multiple predicates
@app.restful_handler(app.is_post(), app.url("api/users"))
async def create_user(context: RESTfulContext, db: IDatabase):
    user_data = context.to_json()
    user = await db.create_user_async(user_data)
    return {"user": user}

# ✅ GOOD - Using predicate helpers
@app.restful_handler(app.post("api/users"))  # Combines is_post() + url()
async def create_user(context: RESTfulContext, db: IDatabase):
    user_data = context.to_json()
    user = await db.create_user_async(user_data)
    return {"user": user}
```

### Service Implementation

```python
# ✅ GOOD - Constructor injection with type hints
class UserService(IUserService):
    def __init__(self, logger: ILogger, db: IDatabase):
        self.logger = logger
        self.db = db

    async def get_user(self, user_id: int):
        self.logger.log(f"Getting user {user_id}")
        return await self.db.fetch_user_async(user_id)

# ❌ BAD - Manual dependencies, no DI
class UserService(IUserService):
    def __init__(self):
        self.logger = ConsoleLogger()  # Don't hardcode!
        self.db = PostgresDB()         # Don't hardcode!
```

### Context Usage

```python
# ✅ GOOD - Use context properties
@app.restful_handler(app.get("api/users/:user_id"))
async def get_user(context: RESTfulContext):
    user_id = context.url_segments["user_id"]
    db = context.open_sql_connection("main")
    user = await db.get_user_async(user_id)
    return {"user": user}

# ✅ BETTER - Inject services via type hints (preferred)
@app.restful_handler(app.get("api/users/:user_id"))
async def get_user(context: RESTfulContext, db: IDatabase):
    user_id = context.url_segments["user_id"]
    user = await db.get_user_async(user_id)
    return {"user": user}
```

## Database Integration

### Connection Management

```python
# In context (legacy approach)
sql_db = context.open_sql_connection("connection_key")
mongo_db = context.open_mongo_connection("mongo_key")
restful = context.open_restful_connection("api_key")
rabbit = context.open_rabbit_connection("rabbit_key")

# Connection keys defined in host.json or options dict
```

### DbManager Configuration

```python
options = {
    "server": "localhost:8080",
    "db": {
        "main": {
            "type": "sql",
            "connection_string": "postgresql://user:pass@localhost/db"
        },
        "mongo": {
            "type": "mongo",
            "connection_string": "mongodb://localhost:27017"
        }
    }
}
```

### Preferred Pattern (DI)

```python
# 1. Define database interface
class IDatabase(ABC):
    @abstractmethod
    async def get_user_async(self, user_id: int) -> dict:
        pass

# 2. Implement database service
class PostgresDatabase(IDatabase):
    def __init__(self, config: IConfig):
        self.connection_string = config.get("db_connection_string")

    async def get_user_async(self, user_id: int) -> dict:
        # Use asyncpg or similar
        async with asyncpg.connect(self.connection_string) as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id)

# 3. Register as scoped service
app.add_scoped(IDatabase, PostgresDatabase)

# 4. Inject in handlers
@app.restful_handler(app.get("api/users/:user_id"))
async def get_user(context: RESTfulContext, db: IDatabase):
    user_id = int(context.url_segments["user_id"])
    user = await db.get_user_async(user_id)
    return {"user": user}
```

## Testing and Development

### Development Server

```python
from bclib import edge

# Simple dev server
app = edge.from_options({
    "server": "localhost:8080"
})

# Register handlers...
@app.restful_handler(app.get("api/hello"))
async def hello(context: RESTfulContext):
    return {"message": "Hello World"}

# Start server
app.run()  # Starts async server on http://localhost:8080
```

### Multi-Instance Mode

```python
# Run multiple instances (load balancing)
edge.from_list({
    "instance1": ["python", "app.py", "-n", "instance1"],
    "instance2": ["python", "app.py", "-n", "instance2"]
})
```

### Testing Handlers

```python
import pytest
from bclib.context import RESTfulContext
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_handler():
    # Mock context
    context = Mock(spec=RESTfulContext)
    context.url_segments = {"user_id": "123"}

    # Mock services
    logger = Mock(spec=ILogger)
    db = Mock(spec=IDatabase)
    db.get_user_async.return_value = {"id": 123, "name": "Test"}

    # Call handler
    result = await get_user(context, logger, db)

    assert result == {"user": {"id": 123, "name": "Test"}}
    db.get_user_async.assert_called_once_with("123")
```

## Common Patterns

### Service Layer Pattern

```python
# 1. Define interface
from abc import ABC, abstractmethod

class IUserService(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> dict:
        pass

    @abstractmethod
    async def create_user(self, user_data: dict) -> dict:
        pass

# 2. Implement service
class UserService(IUserService):
    def __init__(self, logger: ILogger, db: IDatabase):
        self.logger = logger
        self.db = db

    async def get_user(self, user_id: int) -> dict:
        self.logger.log(f"Fetching user {user_id}")
        return await self.db.fetch_user_async(user_id)

    async def create_user(self, user_data: dict) -> dict:
        self.logger.log(f"Creating user {user_data['username']}")
        return await self.db.create_user_async(user_data)

# 3. Register service
app.add_scoped(IUserService, UserService)

# 4. Use in handlers
@app.restful_handler(app.get("api/users/:user_id"))
async def get_user(context: RESTfulContext, user_service: IUserService):
    user_id = int(context.url_segments["user_id"])
    user = await user_service.get_user(user_id)
    return {"user": user}

@app.restful_handler(app.post("api/users"))
async def create_user(context: RESTfulContext, user_service: IUserService):
    user_data = context.to_json()
    user = await user_service.create_user(user_data)
    return {"user": user}
```

### Error Handling

```python
from bclib.exception import HandlerNotFoundErr, ShortCircuitErr

@app.restful_handler(app.get("api/data"))
async def get_data(context: RESTfulContext, logger: ILogger):
    try:
        # Business logic
        data = await fetch_data()
        return {"data": data}
    except ShortCircuitErr:
        # Early exit from pipeline (framework-level)
        raise
    except ValueError as ex:
        # Business logic error
        logger.error(f"Validation error: {ex}")
        return {"error": str(ex)}, 400
    except Exception as ex:
        # Unexpected error
        logger.error(f"Unexpected error: {ex}")
        return {"error": "Internal server error"}, 500
```

### Static Files

```python
from bclib.utility import StaticFileHandler

# Configure in dispatcher
app.static_file_handler = StaticFileHandler("./public")

# Static files served automatically from ./public/
# Example: http://localhost:8080/css/style.css → ./public/css/style.css
```

### WebSocket Communication

```python
@app.websocket_handler(app.url("ws/chat"))
async def chat_handler(context: WebSocketContext):
    # Get session
    session = context.session

    # Send message to client
    await session.send_async("Welcome to chat!")

    # Broadcast to all sessions
    manager = context.websocket_manager
    await manager.broadcast_async("User joined", exclude=[session])
```

### Background Tasks

```python
@app.background_task()
async def periodic_cleanup(logger: ILogger, db: IDatabase):
    # Runs on startup
    while True:
        await asyncio.sleep(3600)  # Every hour
        logger.log("Running cleanup...")
        await db.cleanup_old_records_async()

@app.background_task()
async def startup_task(config: IConfig):
    # Runs once on startup
    config.log("Application started")
```

## Multi-Listener Architecture

### Composition Pattern (New in v3.37.0)

The framework now uses **composition over inheritance**:

```python
# Single Dispatcher with multiple listeners
app = edge.from_options({
    "server": "localhost:8080",      # Adds HttpListener
    "receiver": "localhost:8081",
    "sender": "localhost:8082"        # Adds TcpListener
})

# Both HTTP and Socket listeners active simultaneously!
```

### Listener Collection

Internally, Dispatcher maintains a listener collection:

```python
# In Dispatcher class
self.__listeners: list = []

# Listeners added via:
def add_listener(self, listener):
    self.__listeners.append(listener)

# All listeners initialized:
def initialize_task(self):
    self.__ensure_router_initialized()
    for listener in self.__listeners:
        listener.initialize_task(self.event_loop)
```

### Backward Compatibility

Old code still works via aliases:

```python
# Old pattern (still works)
from bclib.dispatcher import DevServerDispatcher
app = DevServerDispatcher(options)  # → Dispatcher + HttpListener

# New pattern (preferred)
from bclib import edge
app = edge.from_options(options)    # → Dispatcher + appropriate listeners
```

## Key Differences from Generic Frameworks

1. **Composition-based architecture** - Single Dispatcher, multiple listeners
2. **No manual router configuration needed** - Auto-generated from handlers
3. **Predicate-based routing** - More flexible than simple URL matching
4. **Integrated DI container** - No external DI framework needed
5. **Multi-protocol support** - HTTP, WebSocket, Socket, RabbitMQ simultaneously
6. **Context-based handlers** - Different context types for different protocols
7. **Scoped services per request** - Each request gets its own service scope
8. **Pattern-based context detection** - Automatic multi-context routing

## Important Notes

- Property name is `exprossion` not `expression` (typo in `Predicate` base class)
- WebContext handlers must return **strings** (HTML), not dicts
- RESTfulContext handlers must return **dict/list** (JSON), not strings
- Router rebuilds automatically unless manually configured
- Services injected by **type hints**, not parameter names
- Always use **async/await** for I/O operations
- Context is always **first parameter** in handlers (except background tasks)
- Multiple listeners can coexist on same Dispatcher (HTTP + Socket + Rabbit)
- Dispatcher initialization happens in `initialize_task()` before listeners start

## Version History

- **v3.37.0+** - Unified Dispatcher with listener composition pattern
- **v3.36.x and earlier** - Inheritance-based dispatcher hierarchy (deprecated)

## Migration Guide (v3.36 → v3.37)

### Old Pattern (Inheritance)

```python
from bclib.dispatcher import DevServerDispatcher, SocketDispatcher

# HTTP server
app = DevServerDispatcher(options)

# Socket server
app = SocketDispatcher(options)
```

### New Pattern (Composition)

```python
from bclib import edge

# HTTP server
app = edge.from_options({"server": "localhost:8080"})

# Socket server
app = edge.from_options({
    "receiver": "localhost:8081",
    "sender": "localhost:8082"
})

# Both simultaneously!
app = edge.from_options({
    "server": "localhost:8080",
    "receiver": "localhost:8081",
    "sender": "localhost:8082"
})
```

**No code changes required** - Old imports still work via aliases.

---

## Code Review Guidelines

When reviewing or refactoring files in this project, follow these steps:

### 1. Import Optimization

**Move type-hint-only imports to TYPE_CHECKING block:**

```python
# ❌ Bad - Runtime import for type hints only
from bclib.dispatcher.idispatcher import IDispatcher
from bclib.listener.http.http_message import HttpMessage

def __init__(self, dispatcher: IDispatcher, message: HttpMessage):
    pass

# ✅ Good - TYPE_CHECKING block for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.listener.http.http_message import HttpMessage

def __init__(self, dispatcher: 'IDispatcher', message: 'HttpMessage'):
    pass
```

**Benefits:**

- Prevents circular imports
- Improves module load performance
- Separates runtime dependencies from type-checking dependencies
- Standard Python typing best practice

**Rule:** If an import is ONLY used in:

- Type hints (function parameters, return types)
- Class attributes with type annotations
- Variable type annotations

**Rule:** If an import is ONLY used in:

- Type hints (function parameters, return types)
- Class attributes with type annotations
- Variable type annotations

Then move it to `TYPE_CHECKING` block and quote the type in annotations.

**Prefer Interfaces over Concrete Classes:**

When a type has both a concrete class and an interface, prefer using the interface in type hints:

```python
# ❌ Bad - Using concrete class in type hint
from bclib.dispatcher.dispatcher import Dispatcher

def __init__(self, dispatcher: Dispatcher):
    pass

# ✅ Good - Using interface for loose coupling
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher

def __init__(self, dispatcher: 'IDispatcher'):
    pass
```

**Common Interface Patterns in BasisCore:**

- `Dispatcher` → `IDispatcher`
- `ServiceProvider` → `IServiceProvider`
- `CacheManager` → `ICacheManager`
- `Logger` → `ILogger`
- `DatabaseConnection` → `IDatabase`

**Benefits:**

- Loose coupling - code depends on abstractions, not implementations
- Better testability - easier to mock interfaces
- More flexible - can swap implementations without changing type hints
- Follows SOLID principles (Dependency Inversion)

### 2. Remove Unused Imports

- Check all imports at the top of the file
- Remove any imports that are not used anywhere in the code
- Verify with IDE/linter that removal doesn't break anything

### 3. Performance & Technical Review

Check for:

**Performance Issues:**

- ❌ Synchronous I/O in async functions (use `await` for DB, file, network operations)
- ❌ Large loops without chunking/pagination
- ❌ Repeated expensive operations inside loops (move outside if possible)
- ❌ Missing `await` on async calls
- ❌ Unnecessary deepcopy operations

**Technical Issues:**

- ❌ Circular imports (beyond type hints)
- ❌ Mutable default arguments (`def func(items=[])` → use `None` and create inside)
- ❌ Missing error handling for I/O operations
- ❌ SQL injection vulnerabilities (use parameterized queries)
- ❌ Hardcoded credentials or secrets
- ❌ Missing type hints on public functions/methods

### 4. Documentation Review

Add comprehensive docstrings to:

**Module Level (top of file):**

````python
"""
Module Name - Brief description

Detailed description of the module's purpose and functionality.

Key Features:
    - Feature 1
    - Feature 2
    - Feature 3

Example:
    ```python
    from bclib.context import HttpContext

    @app.http_action(app.url("api/example"))
    async def handler(context: HttpContext):
        return {"status": "ok"}
    ```
"""
````

**Class Level:**

````python
class ClassName:
    """
    Brief description of the class

    Detailed explanation of class purpose, behavior, and usage patterns.

    Attributes:
        attr1 (type): Description of attribute
        attr2 (type): Description of attribute

    Args:
        param1: Description
        param2: Description

    Example:
        ```python
        obj = ClassName(param1, param2)
        result = obj.method()
        ```

    Note:
        Any important notes or warnings
    """
````

**Method/Function Level:**

````python
def method_name(self, param1: str, param2: int) -> dict:
    """
    Brief description of what the method does

    Detailed explanation of the method's behavior, side effects,
    and important details.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Returns:
        dict: Description of return value

    Raises:
        ValueError: When this happens
        TypeError: When that happens

    Example:
        ```python
        result = obj.method_name("value", 42)
        print(result["key"])
        ```

    Note:
        Important notes about usage, performance, or behavior
    """
````

**Documentation Standards:**

- Every public class, method, and function must have a docstring
- Include type hints in signatures (not just in docstrings)
- Provide at least one practical example for complex methods
- Document side effects (modifies state, I/O operations, etc.)
- Note any performance considerations
- Explain parameter constraints and valid ranges

### 5. Class Member Organization

Organize class members in a consistent, logical order for better readability and maintainability:

**Standard Order:**

1. **Class-level constants** (ALL_CAPS naming)
2. **Class variables** (shared across instances)
3. **`__init__` constructor** (always first method)
4. **Special/Magic methods** (`__str__`, `__repr__`, `__len__`, etc.)
5. **Properties** (`@property` decorated methods)
6. **Public methods** (main API methods)
7. **Private methods** (methods starting with `_` or `__`)
8. **Static methods** (`@staticmethod`)
9. **Class methods** (`@classmethod`)

**Example:**

```python
class MyClass:
    """Class docstring"""

    # 1. Class constants
    MAX_SIZE = 1000
    DEFAULT_TIMEOUT = 30

    # 2. Class variables
    instance_count = 0

    # 3. Constructor
    def __init__(self, name: str):
        self.name = name
        MyClass.instance_count += 1

    # 4. Special methods
    def __str__(self) -> str:
        return f"MyClass({self.name})"

    def __repr__(self) -> str:
        return f"MyClass(name={self.name!r})"

    # 5. Properties
    @property
    def display_name(self) -> str:
        return self.name.upper()

    # 6. Public methods
    def process(self, data: dict) -> dict:
        """Process data"""
        return self._internal_process(data)

    def validate(self) -> bool:
        """Validate instance"""
        return len(self.name) > 0

    # 7. Private methods
    def _internal_process(self, data: dict) -> dict:
        """Internal processing logic"""
        return data

    def __cleanup(self) -> None:
        """Private cleanup logic"""
        pass

    # 8. Static methods
    @staticmethod
    def parse_config(config: str) -> dict:
        """Parse configuration string"""
        return json.loads(config)

    # 9. Class methods
    @classmethod
    def from_config(cls, config: dict) -> 'MyClass':
        """Create instance from config"""
        return cls(config['name'])
```

**Benefits:**

- Predictable structure - easier to navigate large classes
- Constructor always at the top - first thing developers look for
- Logical grouping - related methods stay together
- Public API separated from internal implementation
- Follows Python conventions and PEP 8 spirit

**Additional Guidelines:**

- Group related methods together (e.g., all CRUD operations)
- Add blank line between method groups
- Consider splitting very large classes into smaller ones
- Use comments to mark sections (e.g., `# Public API methods`)

### 6. Naming Conventions & Standards

Follow Python naming conventions (PEP 8) and ensure names are clear, consistent, and meaningful:

**Variable and Function Names:**

```python
# ✅ Good - snake_case for variables and functions
user_count = 10
def get_user_name(user_id: int) -> str:
    pass

# ❌ Bad - camelCase or inconsistent naming
userCount = 10
def getUserName(userId: int) -> str:
    pass
```

**Class Names:**

```python
# ✅ Good - PascalCase for classes
class UserManager:
    pass

class HttpContext:
    pass

# ❌ Bad - snake_case or other styles
class user_manager:
    pass

class httpContext:
    pass
```

**Constants:**

```python
# ✅ Good - ALL_CAPS for constants
MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30

# ❌ Bad - lowercase or camelCase
max_connections = 100
defaultTimeout = 30
```

**Private Members:**

```python
# ✅ Good - single underscore for internal/protected
def _internal_method(self):
    pass

self._cache = {}

# ✅ Good - double underscore for name mangling (truly private)
def __private_method(self):
    pass

self.__internal_state = None

# ❌ Bad - no underscore for private members
def privateMethod(self):
    pass
```

**Common Naming Issues to Fix:**

1. **Typos in names:**

   - `exprossion` → `expression` (fix if possible without breaking API)
   - `usre` → `user`
   - `mesage` → `message`

2. **Ambiguous names:**

   - `data` → `user_data`, `request_data`, `response_data` (be specific)
   - `temp` → `temporary_result`, `temp_user` (explain what it is)
   - `obj` → `user_object`, `context_object` (be descriptive)

3. **Inconsistent naming:**

   - Mix of `get_user` and `fetch_user` → choose one pattern
   - Mix of `user_id` and `userId` → use snake_case consistently

4. **Boolean naming:**

   ```python
   # ✅ Good - use is_, has_, can_, should_ prefixes
   is_active: bool
   has_permission: bool
   can_edit: bool
   should_retry: bool

   # ❌ Bad - ambiguous names
   active: bool
   permission: bool
   edit: bool
   ```

5. **Method names should be verbs:**

   ```python
   # ✅ Good - action verbs
   def calculate_total(self) -> float:
       pass

   def validate_input(self, data: dict) -> bool:
       pass

   # ❌ Bad - nouns or unclear
   def total(self) -> float:
       pass

   def input(self, data: dict) -> bool:
       pass
   ```

**Naming Checklist:**

- [ ] Variables and functions use `snake_case`
- [ ] Classes use `PascalCase`
- [ ] Constants use `ALL_CAPS`
- [ ] Private members start with `_` or `__`
- [ ] Boolean variables use `is_`, `has_`, `can_`, `should_` prefixes
- [ ] Method names are verbs (action-oriented)
- [ ] Names are descriptive and unambiguous
- [ ] No typos in identifiers
- [ ] Consistent naming patterns throughout the file
- [ ] Abbreviations avoided unless widely recognized (e.g., `url`, `id`, `http`)

### Complete Review Checklist

When asked to "review/check a file", perform ALL these steps:

- [ ] Move type-hint-only imports to `TYPE_CHECKING` block
- [ ] Quote type hints that are moved to `TYPE_CHECKING`
- [ ] **Replace concrete classes with interfaces in type hints** (Dispatcher→IDispatcher, etc.)
- [ ] Remove unused imports
- [ ] **Organize class members in standard order** (constants, **init**, properties, public, private, static, classmethod)
- [ ] **Check naming conventions** (snake_case, PascalCase, ALL_CAPS, fix typos)
- [ ] **Verify method/variable names are descriptive and follow verb/noun patterns**
- [ ] Check for performance issues (sync I/O, inefficient loops, etc.)
- [ ] Check for technical issues (circular imports, mutable defaults, etc.)
- [ ] Verify error handling for I/O operations
- [ ] **Add/complete module-level docstring with description, features, and examples**
- [ ] **Add/complete class-level docstrings with attributes, args, and examples**
- [ ] **Add/complete method/function docstrings with Args, Returns, Raises, Examples, Notes**
- [ ] Verify all public APIs have type hints
- [ ] Check for security issues (SQL injection, hardcoded secrets, etc.)

### Command Translation

When user says (in Persian or English):

- "فایل X رو بررسی کن" / "Review file X"
- "این فایل رو چک کن" / "Check this file"
- "کد رو بهینه کن" / "Optimize the code"

Perform the **Complete Review Checklist** above.

---
