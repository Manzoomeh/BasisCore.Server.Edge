# Dependency Injection (DI) in BasisCore.Edge

This directory contains examples demonstrating how to use Dependency Injection with BasisCore.Edge web server.

## What is Dependency Injection?

Dependency Injection is a design pattern that helps you create loosely coupled, testable code by:

- Separating interface definitions from implementations
- Managing object lifetime and dependencies
- Making code easier to test, maintain, and extend

## ⭐ NEW: Automatic Handler Parameter Injection

**BasisCore.Edge now supports automatic dependency injection directly into handler parameters!**

Instead of manually calling `context.get_service()`, you can simply add type-hinted parameters to your handler functions, and services will be automatically injected:

```python
# ❌ Old way - manual service resolution
@app.restful_handler()
async def handler(context: RESTfulContext):
    logger = context.get_service(ILogger)
    db = context.get_service(IDatabase)

    logger.log("Processing...")
    result = await db.query("SELECT ...")
    return {"data": result}

# ✅ New way - automatic injection
@app.restful_handler()
async def handler(
    context: RESTfulContext,
    logger: ILogger,
    db: IDatabase
):
    logger.log("Processing...")
    result = await db.query("SELECT ...")
    return {"data": result}
```

**Benefits:**

- ✅ Cleaner, more readable code
- ✅ No boilerplate service resolution
- ✅ Explicit dependencies in function signature
- ✅ Better IDE support (autocomplete, type checking)
- ✅ Easier to test (can call handlers directly with mock services)
- ✅ Works with all handler decorators (`@restful_handler`, `@web_handler`, `@socket_action`, etc.)

**See:** `auto_injection.py` for complete examples

## Service Lifetimes

BasisCore.Edge supports three service lifetimes:

### 1. **Singleton** (یک نمونه برای کل برنامه)

- One instance created for the entire application lifetime
- Same instance shared across all requests
- Best for: Configuration, logging, caching services
- Memory efficient for stateless services

### 2. **Scoped** (یک نمونه برای هر درخواست)

- One instance created per HTTP request
- New instance for each request, shared within that request
- Best for: Database connections, request-specific data
- Automatic cleanup after request completes

### 3. **Transient** (نمونه جدید در هر استفاده)

- New instance created every time service is requested
- Best for: Lightweight, stateless utilities
- Useful when you need fresh state each time

## Constructor Injection (تزریق خودکار وابستگی‌ها)

BasisCore.Edge از **Constructor Injection با Type Hints** پشتیبانی می‌کند. این به معنای آن است که وابستگی‌های یک کلاس به طور خودکار از روی type hints کانستراکتور تشخیص داده و inject می‌شوند.

### مزایای Constructor Injection:

- **بدون نیاز به Factory Function**: دیگر نیازی به نوشتن lambda نیست
- **کد تمیزتر**: ثبت سرویس ساده‌تر می‌شود
- **Type-Safe**: با استفاده از type hints امنیت تایپی دارید
- **قابل نگهداری بهتر**: اضافه کردن dependency جدید آسان‌تر است
- **پشتیبانی IDE**: Autocomplete و type checking بهتر

### مثال Constructor Injection:

```python
# تعریف سرویس با Type Hints
class TimeService(ITimeService):
    def __init__(self, logger: ILogger, config: IConfig):
        # وابستگی‌ها به طور خودکار inject می‌شوند
        self.logger = logger
        self.config = config

# ثبت ساده - بدون factory!
services.add_singleton(ITimeService, TimeService)

# قبلاً باید این کار را می‌کردید:
# services.add_singleton(
#     ITimeService,
#     factory=lambda: TimeService(
#         logger=services.get_service(ILogger),
#         config=services.get_service(IConfig)
#     )
# )
```

## Method Injection (فراخوانی متدها با DI)

علاوه بر Constructor Injection، می‌توانید **هر تابع یا متدی** را با DI فراخوانی کنید:

### مزایای Method Injection:

- **توابع خالص**: business logic بدون وابستگی به DI نوشته می‌شود
- **تست آسان**: می‌توانید توابع را مستقیماً با mock ها فراخوانی کنید
- **انعطاف‌پذیر**: ترکیب پارامترهای injected و provided
- **بدون تغییر کد**: با توابع موجود کار می‌کند

### مثال Method Injection:

```python
# تابع معمولی با type hints
def process_order(logger: ILogger, db: IDatabase, order_data: dict):
    logger.log(f"Processing order: {order_data}")
    db.save(order_data)
    return {"status": "success"}

# فراخوانی با DI - logger و db خودکار inject می‌شوند
result = services.invoke_method(
    process_order,
    order_data={"id": "ORD-001"}
)

# برای async functions
async def async_process(logger: ILogger, data: dict):
    logger.log("Processing...")
    return await do_something(data)

result = await services.invoke_method_async(async_process, data={...})
```

### Smart Invoke - تشخیص خودکار Sync/Async ⭐ توصیه می‌شود

به جای استفاده از `invoke_method` یا `invoke_method_async`، می‌توانید از **`invoke()`** استفاده کنید که خودش تشخیص می‌دهد تابع async است یا sync:

```python
# یک متد برای همه - خودکار تشخیص می‌دهد!
def sync_func(logger: ILogger, data: str):
    logger.log(data)
    return "done"

async def async_func(logger: ILogger, db: IDatabase):
    await db.save()
    return "saved"

# Smart invoke - هر دو را پشتیبانی می‌کند
result = services.invoke(sync_func, data="test")      # Sync
result = await services.invoke(async_func)             # Async

# نیازی نیست بدانید تابع async است یا sync!
result = await services.invoke(some_function, param="value")
```

### روش‌های Method Injection:

| متد                     | استفاده               | توصیه                      |
| ----------------------- | --------------------- | -------------------------- |
| `invoke()`              | خودکار (sync و async) | ⭐ توصیه می‌شود            |
| `invoke_method()`       | فقط sync              | وقتی مطمئن هستید sync است  |
| `invoke_method_async()` | فقط async             | وقتی مطمئن هستید async است |

### تفاوت Constructor vs Method Injection:

| ویژگی   | Constructor Injection    | Method Injection           |
| ------- | ------------------------ | -------------------------- |
| استفاده | ساخت instance کلاس       | فراخوانی تابع/متد          |
| ثبت     | `services.add_xxx(Type)` | `services.invoke(func)` ⭐ |
| کاربرد  | سرویس‌ها و کلاس‌ها       | Business logic functions   |
| تست     | Mock کردن services       | فراخوانی مستقیم تابع       |

### مقایسه روش‌های ثبت سرویس:

| ویژگی        | با ارث‌بری (\_configure_services) | بدون ارث‌بری (configure_services) ⭐   |
| ------------ | --------------------------------- | -------------------------------------- |
| نیاز به کلاس | ✅ باید کلاس جدید بسازید          | ❌ مستقیماً از dispatcher استفاده کنید |
| خطوط کد      | بیشتر (class + override)          | کمتر (فقط تابع)                        |
| مناسب برای   | برنامه‌های بزرگ و پیچیده          | برنامه‌های کوچک و prototype            |
| انعطاف       | کنترل کامل                        | ساده و سریع                            |
| یادگیری      | نیاز به درک OOP                   | ساده‌تر                                |

## How to Use DI

### Step 1: Define Service Interfaces

```python
from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass

class IDatabase(ABC):
    @abstractmethod
    async def query(self, sql: str):
        pass
```

### Step 2: Implement Services (با Constructor Injection)

```python
class ConsoleLogger(ILogger):
    def __init__(self):
        # سرویس بدون وابستگی
        pass

    def log(self, message: str):
        print(f"[LOG] {message}")

class PostgresDatabase(IDatabase):
    def __init__(self, logger: ILogger):
        # logger به طور خودکار inject می‌شود
        self.logger = logger
        self.logger.log("Database initialized")

    async def query(self, sql: str):
        self.logger.log(f"Executing: {sql}")
        # Database logic here
        pass

class UserService:
    def __init__(self, logger: ILogger, db: IDatabase):
        # همه وابستگی‌ها به طور خودکار inject می‌شوند
        self.logger = logger
        self.db = db
        self.logger.log("UserService initialized")
```

### Step 3: Register Services in Dispatcher

دو روش برای ثبت سرویس‌ها:

#### روش 1: بدون ارث‌بری (ساده‌تر) ⭐ توصیه می‌شود

```python
from bclib import edge
from bclib.utility import ServiceProvider

# ایجاد dispatcher بدون ارث‌بری
app = edge.DevServerDispatcher(options)

# تابع setup
def setup_services(services: ServiceProvider):
    services.add_singleton(ILogger, ConsoleLogger)
    services.add_scoped(IDatabase, PostgresDatabase)
    services.add_transient(UserService)

# ثبت سرویس‌ها - بدون نیاز به کلاس جدید!
app.configure_services(setup_services)

# یا inline با lambda
app.configure_services(lambda services: (
    services.add_singleton(ILogger, ConsoleLogger),
    services.add_scoped(IDatabase, PostgresDatabase)
))
```

#### روش 2: با ارث‌بری (برای برنامه‌های پیچیده)

````python
from bclib import edge
from bclib.utility import ServiceProvider

class MyDispatcher(edge.DevServerDispatcher):
    def _configure_services(self, services: ServiceProvider):
        # ثبت سرویس‌ها - وابستگی‌ها خودکار resolve می‌شوند!

        # Register singleton (one instance for app)
        services.add_singleton(ILogger, ConsoleLogger)

        # Register scoped (one instance per request)
        # PostgresDatabase نیاز به ILogger دارد - خودکار inject می‌شود!
        services.add_scoped(IDatabase, PostgresDatabase)

        # Register transient (new instance each time)
        # UserService نیاز به ILogger و IDatabase دارد - خودکار!
        services.add_transient(UserService)

app = MyDispatcher(options)
```### Step 4: Use Services in Handlers

```python
@app.restful_handler()
async def my_handler(context: RESTfulContext):
    # Get services from DI container
    logger = context.get_service(ILogger)
    db = context.get_service(IDatabase)

    # Use services
    logger.log("Processing request...")
    result = await db.query("SELECT * FROM users")

    return {"data": result}
````

## Registration Patterns

### By Implementation Type (با Constructor Injection)

```python
# ساده‌ترین روش - وابستگی‌ها خودکار inject می‌شوند
services.add_singleton(ILogger, ConsoleLogger)
services.add_scoped(IDatabase, PostgresDatabase)  # نیاز به ILogger - خودکار!
services.add_transient(UserService)  # نیاز به ILogger و IDatabase - خودکار!
```

### By Factory Function (برای کنترل دستی)

```python
# اگر نیاز به کنترل دستی دارید
services.add_singleton(
    ILogger,
    factory=lambda: ConsoleLogger(log_level="DEBUG")
)
```

### By Pre-created Instance

```python
# برای singletonهایی که قبلاً ساختید
logger = ConsoleLogger()
services.add_singleton(ILogger, instance=logger)
```

### Constructor Injection vs Factory Function

```python
# ❌ روش قدیمی - نیاز به factory function
services.add_transient(
    IGreetingService,
    factory=lambda: GreetingService(
        logger=services.get_service(ILogger),
        time_service=services.get_service(ITimeService)
    )
)

# ✅ روش جدید - خودکار با type hints
class GreetingService:
    def __init__(self, logger: ILogger, time_service: ITimeService):
        self.logger = logger
        self.time_service = time_service

services.add_transient(GreetingService)  # همین!
```

## Examples in This Directory

### `no_inheritance.py` 🆕 بدون ارث‌بری!

مثال کامل **DI بدون نیاز به ارث‌بری**:

- استفاده از `app.configure_services(callback)`
- بدون نیاز به ساخت کلاس derived
- مناسب برای برنامه‌های ساده و prototype
- کد کمتر و ساده‌تر

**اجرا:**

```bash
python test/di/no_inheritance.py
```

**Test endpoints:**

- `GET http://localhost:8095/hello` - DI بدون inheritance
- `GET http://localhost:8095/greet/Alice` - سرویس با dependencies
- `GET http://localhost:8095/info` - اطلاعات کامل
- `GET http://localhost:8095/test/chaining` - method chaining

### `method_injection.py` 🔥 جدید!

مثال کامل **Method Injection** - فراخوانی متدها با DI:

- فراخوانی توابع با `invoke_method()` و `invoke_method_async()`
- تزریق خودکار پارامترهای type-hinted
- پشتیبانی از توابع sync و async
- ترکیب پارامترهای injected و provided

**اجرا:**

```bash
python test/di/method_injection.py
```

**Test endpoints:**

- `GET http://localhost:8094/calculate` - Smart invoke با sync function
- `POST http://localhost:8094/order` - Smart invoke با async function
- `POST http://localhost:8094/validate` - پارامترهای optional
- `GET http://localhost:8094/method-injection/info` - اطلاعات کامل

**ویژگی ویژه:** همه handlerها از `services.invoke()` استفاده می‌کنند که خودکار تشخیص می‌دهد تابع async است یا sync!

### `constructor_injection.py` ⭐ توصیه می‌شود

مثال کامل **Constructor Injection با Type Hints**:

- تزریق خودکار وابستگی‌ها از روی type hints
- سرویس‌های با وابستگی‌های چندگانه
- زنجیره وابستگی (dependency chain)
- مقایسه روش قدیم و جدید

**اجرا:**

```bash
python test/di/constructor_injection.py
```

**Test endpoints:**

- `GET http://localhost:8093/hello` - تست پایه
- `GET http://localhost:8093/report/daily` - سرویس با 3 dependency
- `GET http://localhost:8093/injection/info` - اطلاعات کامل
- `GET http://localhost:8093/test/dependency-chain` - تست زنجیره وابستگی

### `simple_di.py`

A complete working example demonstrating:

- Interface definitions (ILogger, ITimeService, IGreetingService)
- Concrete implementations
- Service registration with different lifetimes
- Usage in handlers
- Testing singleton vs transient behavior

**Run it:**

```bash
python test/di/simple_di.py
```

**Test endpoints:**

- `GET http://localhost:8092/hello` - Basic DI usage
- `GET http://localhost:8092/greet/John` - DI with parameters
- `GET http://localhost:8092/services/info` - Service information
- `GET http://localhost:8092/test/singleton` - Test singleton lifetime
- `GET http://localhost:8092/test/transient` - Test transient lifetime

## Benefits of Using DI

### 1. **Testability** (قابلیت تست)

Replace real services with mock implementations for testing:

```python
# Production
services.add_singleton(IDatabase, PostgresDatabase)

# Testing
services.add_singleton(IDatabase, MockDatabase)
```

### 2. **Loose Coupling** (کاهش وابستگی)

Code depends on interfaces, not concrete implementations:

```python
# Handler doesn't know about ConsoleLogger implementation
logger = context.get_service(ILogger)
logger.log("Message")  # Works with any ILogger implementation
```

### 3. **Flexibility** (انعطاف‌پذیری)

Easily swap implementations without changing handler code:

```python
# Switch from console to file logging
services.add_singleton(ILogger, FileLogger)  # Instead of ConsoleLogger
```

### 4. **Lifetime Management** (مدیریت چرخه عمر)

Framework manages object creation and disposal:

```python
# Scoped services automatically cleaned up after request
services.add_scoped(IDatabase, PostgresDatabase)
```

## Best Practices

1. **Choose Configuration Method**:
   - ⭐ Use `configure_services()` for simple apps (no inheritance)
   - Use `_configure_services()` override for complex apps with custom logic
2. **Use Interfaces**: Always define abstract interfaces for your services

3. **Choose Right Lifetime**:
   - Singleton for stateless services
   - Scoped for per-request resources
   - Transient for lightweight utilities
4. **Avoid Service Locator**: Use `context.get_service()` in handlers, not in business logic
5. **Constructor Injection**: Pass dependencies through constructors when possible
6. **Test with Mocks**: Create mock implementations for testing

## Common Patterns

### Configuration Service (Singleton)

```python
class IConfig(ABC):
    @abstractmethod
    def get(self, key: str) -> str:
        pass

services.add_singleton(IConfig, JsonConfigService)
```

### Database Connection (Scoped)

```python
class IDatabase(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

services.add_scoped(IDatabase, PostgresDatabase)
```

### Utility Service (Transient)

```python
class IValidator(ABC):
    @abstractmethod
    def validate(self, data: dict) -> bool:
        pass

services.add_transient(IValidator, JsonValidator)
```

## Architecture

```
ServiceProvider (Root Container)
    ↓
RoutingDispatcher
    ├── _configure_services() - Register services
    └── services property - Access container
        ↓
Context (Scoped Container per Request)
    ├── services property - Access scoped services
    └── get_service() - Resolve services
        ↓
Handler
    └── Uses context.get_service() to get dependencies
```

## Advanced Topics

### Service Lifetime Comparison

| Lifetime  | Created     | Shared         | Disposed      | Use Case              |
| --------- | ----------- | -------------- | ------------- | --------------------- |
| Singleton | Once        | App-wide       | At shutdown   | Config, Logger        |
| Scoped    | Per request | Within request | After request | Database, Session     |
| Transient | Every call  | Never          | Immediately   | Utilities, Validators |

### Memory Considerations

- **Singleton**: Lowest memory, but can hold state
- **Scoped**: Moderate memory, automatic cleanup
- **Transient**: Highest memory, no caching

### Thread Safety

- **Singleton**: Must be thread-safe
- **Scoped**: Isolated per request (thread-safe)
- **Transient**: New instance (thread-safe)

## Troubleshooting

### Service Not Registered

```python
# Error: Service not found
logger = context.get_service(ILogger)  # Returns None

# Solution: Register the service
services.add_singleton(ILogger, ConsoleLogger)
```

### Circular Dependencies

```python
# Problem: ServiceA needs ServiceB, ServiceB needs ServiceA
# Solution: Use factory functions with lazy resolution
services.add_transient(
    IServiceA,
    factory=lambda: ServiceA(services.get_service(IServiceB))
)
```

### Scope Issues

```python
# Problem: Using scoped service in singleton
class MySingleton:
    def __init__(self, db: IDatabase):  # WRONG! db is scoped
        self.db = db

# Solution: Get scoped services per-request, not in singleton constructor
```

## Automatic Handler Injection - Complete Guide

### How It Works

When you add type-hinted parameters to your handler functions, the dispatcher automatically:

1. **Analyzes the handler signature** using `inspect.signature()`
2. **Extracts type hints** using `get_type_hints()`
3. **Resolves services** from the DI container based on parameter types
4. **Injects services** as keyword arguments when calling the handler

### Supported Decorators

Automatic DI injection works with ALL handler decorators:

- `@restful_handler()` - RESTful API endpoints
- `@web_handler()` - Legacy web requests
- `@socket_action()` - Socket connections
- `@websocket_handler()` - WebSocket connections
- `@client_source_handler()` - Client source actions
- `@server_source_handler()` - Server source actions
- `@rabbit_handler()` - RabbitMQ message handlers

### Examples

#### Single Service Injection

```python
@app.restful_handler("/users")
async def get_users(context: RESTfulContext, logger: ILogger):
    logger.log("Fetching users...")
    # No need for: logger = context.get_service(ILogger)
    return {"users": [...]}
```

#### Multiple Services Injection

```python
@app.restful_handler("/orders/:id")
async def get_order(
    context: RESTfulContext,
    logger: ILogger,
    db: IDatabase,
    cache: ICacheService
):
    order_id = context.url_segments.id
    logger.log(f"Getting order {order_id}")

    # Check cache first
    cached = cache.get(f"order:{order_id}")
    if cached:
        return cached

    # Query database
    order = await db.query(f"SELECT * FROM orders WHERE id = {order_id}")
    cache.set(f"order:{order_id}", order)

    return {"order": order}
```

#### Mixed Parameters (Context + Services)

```python
@app.restful_handler("/report/:type")
async def generate_report(
    context: RESTfulContext,
    logger: ILogger,
    report_service: IReportService
):
    # Get data from context
    report_type = context.url_segments.type
    query_params = context.url_parameters

    # Use injected services
    logger.log(f"Generating {report_type} report")
    report = await report_service.generate(report_type, query_params)

    return {"report": report}
```

### Comparison: Old vs New

#### Before (Manual Service Resolution)

```python
@app.restful_handler("/process")
async def process_data(context: RESTfulContext):
    # Lots of boilerplate
    logger = context.get_service(ILogger)
    db = context.get_service(IDatabase)
    validator = context.get_service(IValidator)
    notifier = context.get_service(INotifier)

    # Check if services exist
    if not logger or not db or not validator or not notifier:
        return {"error": "Service not available"}

    # Now do actual work
    logger.log("Processing...")
    valid = validator.validate(context.request.body)
    if valid:
        await db.save(context.request.body)
        await notifier.send("Data saved")

    return {"status": "ok"}
```

#### After (Automatic Injection)

```python
@app.restful_handler("/process")
async def process_data(
    context: RESTfulContext,
    logger: ILogger,
    db: IDatabase,
    validator: IValidator,
    notifier: INotifier
):
    # Clean, readable code
    logger.log("Processing...")
    valid = validator.validate(context.request.body)
    if valid:
        await db.save(context.request.body)
        await notifier.send("Data saved")

    return {"status": "ok"}
```

**Benefits:**

- ✅ 50% less code
- ✅ No null checks needed
- ✅ Explicit dependencies
- ✅ Better IDE support
- ✅ Easier to test

### Testing with Automatic Injection

One major benefit is easier testing - you can call handlers directly with mock services:

```python
# Test without starting the server
async def test_handler():
    # Create mocks
    mock_logger = MockLogger()
    mock_db = MockDatabase()
    mock_context = MockContext()

    # Call handler directly with mocks
    result = await get_order(
        context=mock_context,
        logger=mock_logger,
        db=mock_db
    )

    # Assert results
    assert result["order"]["id"] == "123"
    assert mock_logger.log_count == 1
    assert mock_db.query_count == 1
```

### Requirements

For automatic injection to work:

1. ✅ Services must be registered in the DI container
2. ✅ Parameters must have type hints
3. ✅ Type hints must match interface types in DI container
4. ✅ Context parameter should be first (by convention)

### Edge Cases

**Parameters without type hints:** Not injected, you must provide them manually

```python
@app.restful_handler()
async def handler(context, logger):  # No type hints
    # logger will NOT be injected
    logger = context.get_service(ILogger)  # Still need manual resolution
```

**Unregistered services:** Silently skipped, handler called without them

```python
@app.restful_handler()
async def handler(context: RESTfulContext, unknown: IUnknownService):
    # IUnknownService not registered - parameter not provided
    # Handler called with only 'context'
    # Make sure to handle missing parameters
```

**Multiple parameters with same type:** Each gets its own instance (for Transient) or shared instance (for Singleton/Scoped)

## Resources

- **BasisCore.Edge Documentation**: See main project README
- **ASP.NET Core DI**: Similar patterns and concepts
- **Python abc Module**: Abstract base classes for interfaces
- **Type Hints**: Use `Type[T]` and `TypeVar` for type safety

## Example Files

- `simple_di.py` - Basic DI usage
- `constructor_injection.py` - Automatic constructor injection
- `method_injection.py` - Method injection with invoke()
- `no_inheritance.py` - Service registration without inheritance
- `auto_injection.py` - **NEW: Automatic handler parameter injection**

## Test Files

- `test_constructor_injection.py` - Constructor injection tests
- `test_method_injection.py` - Method injection tests
- `test_smart_invoke.py` - Smart invoke tests
- `test_no_inheritance.py` - Non-inheritance registration tests
- `test_auto_injection.py` - **NEW: Automatic handler injection tests**

## Questions?

For more examples and documentation, see:

- `bclib/utility/service_provider.py` - DI container implementation
- `bclib/dispatcher/routing_dispatcher.py` - Dispatcher integration
- `bclib/dispatcher/dispatcher.py` - Handler decorators with automatic DI
- `bclib/context/context.py` - Context integration
