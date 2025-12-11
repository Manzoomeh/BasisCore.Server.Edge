# Multiple Implementations per Interface in DI Container

## Overview

The BasisCore ServiceProvider now supports registering and resolving multiple implementations for a single interface. This feature enables flexible patterns like plugin systems, middleware pipelines, and multi-protocol listeners.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Registration](#registration)
- [Resolution](#resolution)
- [Automatic Injection](#automatic-injection)
- [Lifetime Behavior](#lifetime-behavior)
- [Use Cases](#use-cases)
- [Examples](#examples)
- [API Reference](#api-reference)

---

## Quick Start

### Basic Usage

```python
from bclib.di import ServiceProvider

# Create container
services = ServiceProvider()

# Register multiple implementations for same interface
services.add_singleton(IListener, HttpListener)
services.add_singleton(IListener, TcpListener)
services.add_singleton(IListener, RabbitListener)

# Get first implementation
first_listener = services.get_service(IListener)  # Returns HttpListener

# Get all implementations
all_listeners = services.get_service(list[IListener])  # Returns [HttpListener, TcpListener, RabbitListener]
```

### Automatic Injection

```python
class ListenerFactory:
    def __init__(self, listeners: list[IListener]):
        # Automatically receives all registered IListener implementations
        self.listeners = listeners

services.add_singleton(ListenerFactory)
factory = services.get_service(ListenerFactory)  # Auto-injected with all listeners
```

---

## Core Concepts

### Multiple Registrations

- **Same Interface, Multiple Implementations**: You can call `add_singleton()`, `add_scoped()`, or `add_transient()` multiple times with the same service type
- **Order Matters**: The first registered implementation is returned by default
- **Type-Safe**: Full type hint support with `list[Type]` annotations

### Resolution Strategies

1. **Single Resolution** (`get_service(Type)`): Returns first registered implementation
2. **List Resolution** (`get_service(list[Type])`): Returns all registered implementations
3. **Automatic Injection**: Parameters typed as `list[Type]` are automatically resolved

---

## Registration

### Singleton (One instance per application)

```python
# Register multiple singletons
services.add_singleton(INotificationService, EmailNotificationService)
services.add_singleton(INotificationService, SmsNotificationService)
services.add_singleton(INotificationService, PushNotificationService)
```

### Scoped (One instance per scope/request)

```python
# Register multiple scoped services
services.add_scoped(IMiddleware, AuthMiddleware)
services.add_scoped(IMiddleware, LoggingMiddleware)
services.add_scoped(IMiddleware, ValidationMiddleware)
```

### Transient (New instance every time)

```python
# Register multiple transient services
services.add_transient(INotification, EmailNotification)
services.add_transient(INotification, SmsNotification)
services.add_transient(INotification, PushNotification)
```

### With Factories

```python
# Register with factory functions
services.add_singleton(
    IListener,
    factory=lambda sp, **kwargs: HttpListener({"endpoint": "localhost:8080"})
)
services.add_singleton(
    IListener,
    factory=lambda sp, **kwargs: TcpListener({"endpoint": "localhost:3000"})
)
```

---

## Resolution

### Get First Implementation

```python
# Returns the first registered implementation
listener = services.get_service(IListener)  # HttpListener
```

### Get All Implementations

```python
# Returns list of all implementations
all_listeners = services.get_service(list[IListener])
# Returns: [HttpListener, TcpListener, RabbitListener]

# Iterate over all
for listener in all_listeners:
    listener.start()
```

### Check for Registrations

```python
listeners = services.get_service(list[IListener])

if listeners:
    print(f"Found {len(listeners)} listeners")
else:
    print("No listeners registered")
```

---

## Automatic Injection

### Constructor Injection

The DI container automatically detects `list[Type]` parameters and injects all registered implementations:

```python
class NotificationManager:
    def __init__(self, services: list[INotificationService]):
        # Automatically injected with all INotificationService implementations
        self.services = services

    def broadcast(self, message: str):
        for service in self.services:
            service.send(message)

# Register implementations
services.add_singleton(INotificationService, EmailService)
services.add_singleton(INotificationService, SmsService)
services.add_singleton(INotificationService, PushService)

# Register manager
services.add_singleton(NotificationManager)

# Get manager - automatically receives all notification services
manager = services.get_service(NotificationManager)
manager.broadcast("Important update!")  # Sends via all channels
```

### Mixed Dependencies

```python
class Application:
    def __init__(
        self,
        logger: ILogger,                    # Single service
        listeners: list[IListener],         # All listeners
        config: IConfiguration,             # Single service
        middlewares: list[IMiddleware]      # All middlewares
    ):
        self.logger = logger
        self.listeners = listeners
        self.config = config
        self.middlewares = middlewares
```

---

## Lifetime Behavior

### Singleton

Each implementation is created once and cached:

```python
services.add_singleton(IListener, HttpListener)
services.add_singleton(IListener, TcpListener)

# First call
listeners_1 = services.get_service(list[IListener])

# Second call - same instances
listeners_2 = services.get_service(list[IListener])

assert listeners_1[0] is listeners_2[0]  # True (same HttpListener instance)
assert listeners_1[1] is listeners_2[1]  # True (same TcpListener instance)
```

### Scoped

Each implementation is created once per scope:

```python
services.add_scoped(IMiddleware, AuthMiddleware)
services.add_scoped(IMiddleware, LoggingMiddleware)

# Within same scope
middlewares_1 = services.get_service(list[IMiddleware])
middlewares_2 = services.get_service(list[IMiddleware])

assert middlewares_1[0] is middlewares_2[0]  # True (same scope)

# New scope
services.clear_scope()
middlewares_3 = services.get_service(list[IMiddleware])

assert middlewares_1[0] is not middlewares_3[0]  # False (different scope)
```

### Transient

Each implementation is created every time:

```python
services.add_transient(INotification, EmailNotification)
services.add_transient(INotification, SmsNotification)

notifications_1 = services.get_service(list[INotification])
notifications_2 = services.get_service(list[INotification])

assert notifications_1[0] is not notifications_2[0]  # False (new instances)
assert notifications_1[1] is not notifications_2[1]  # False (new instances)
```

### Mixed Lifetimes

You can mix different lifetimes for the same interface:

```python
services.add_singleton(INotificationService, EmailService)    # Singleton
services.add_transient(INotificationService, SmsService)      # Transient
services.add_scoped(INotificationService, PushService)        # Scoped

# Each service respects its own lifetime
services_1 = services.get_service(list[INotificationService])
services_2 = services.get_service(list[INotificationService])

assert services_1[0] is services_2[0]     # True (singleton)
assert services_1[1] is not services_2[1] # False (transient)
assert services_1[2] is services_2[2]     # True (scoped)
```

---

## Use Cases

### 1. Multi-Protocol Listeners

```python
# Register listeners for different protocols
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    HttpListener({"endpoint": "localhost:8080"}))
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    TcpListener({"endpoint": "localhost:3000"}))
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    RabbitListener({"queue": "tasks"}))

class ListenerFactory:
    def __init__(self, listeners: list[IListener]):
        self.listeners = listeners

    def start_all(self, event_loop):
        for listener in self.listeners:
            listener.initialize_task(event_loop)

services.add_singleton(ListenerFactory)
factory = services.get_service(ListenerFactory)
```

### 2. Middleware Pipeline

```python
# Register middleware in order
services.add_scoped(IMiddleware, AuthenticationMiddleware)
services.add_scoped(IMiddleware, AuthorizationMiddleware)
services.add_scoped(IMiddleware, LoggingMiddleware)
services.add_scoped(IMiddleware, ValidationMiddleware)

class MiddlewarePipeline:
    def __init__(self, middlewares: list[IMiddleware]):
        self.middlewares = middlewares

    async def execute(self, context):
        for middleware in self.middlewares:
            await middleware.invoke(context)
```

### 3. Plugin System

```python
# Register plugins
services.add_singleton(IPlugin, AuthenticationPlugin)
services.add_singleton(IPlugin, CachePlugin)
services.add_singleton(IPlugin, MetricsPlugin)

class PluginManager:
    def __init__(self, plugins: list[IPlugin]):
        self.plugins = plugins

    async def initialize_all(self):
        for plugin in self.plugins:
            await plugin.initialize()
```

### 4. Multi-Channel Notifications

```python
# Register notification channels
services.add_singleton(INotificationService, EmailNotificationService)
services.add_singleton(INotificationService, SmsNotificationService)
services.add_singleton(INotificationService, PushNotificationService)
services.add_singleton(INotificationService, SlackNotificationService)

class NotificationManager:
    def __init__(self, services: list[INotificationService]):
        self.services = services

    async def broadcast(self, message: str, priority: str = "normal"):
        # Send to all channels based on priority
        channels = self.services if priority == "high" else self.services[:2]
        for service in channels:
            await service.send(message)
```

### 5. Multiple HTTP Listeners on Different Ports

```python
# Register HTTP listeners for different endpoints
http_configs = [
    {"endpoint": "localhost:8080"},
    {"endpoint": "localhost:8081"},
    {"endpoint": {"url": "0.0.0.0", "port": 443}}
]

for config in http_configs:
    services.add_singleton(IListener, factory=lambda sp, cfg=config, **kwargs:
        HttpListener(cfg))

# All listeners will be started automatically
factory = services.get_service(ListenerFactory)
```

---

## Examples

### Complete Example: Notification System

```python
from abc import ABC, abstractmethod
from bclib.di import ServiceProvider

# Define interface
class INotificationService(ABC):
    @abstractmethod
    def send(self, message: str) -> str:
        pass

# Implementations
class EmailNotificationService(INotificationService):
    def send(self, message: str) -> str:
        return f"Email: {message}"

class SmsNotificationService(INotificationService):
    def send(self, message: str) -> str:
        return f"SMS: {message}"

class PushNotificationService(INotificationService):
    def send(self, message: str) -> str:
        return f"Push: {message}"

# Manager that uses all services
class NotificationManager:
    def __init__(self, services: list[INotificationService]):
        self.services = services

    def broadcast(self, message: str):
        results = []
        for service in self.services:
            results.append(service.send(message))
        return results

# Setup DI
services = ServiceProvider()

# Register implementations
services.add_singleton(INotificationService, EmailNotificationService)
services.add_singleton(INotificationService, SmsNotificationService)
services.add_singleton(INotificationService, PushNotificationService)

# Register manager
services.add_singleton(NotificationManager)

# Use
manager = services.get_service(NotificationManager)
results = manager.broadcast("Important update!")
# Results: ["Email: Important update!", "SMS: Important update!", "Push: Important update!"]
```

### Complete Example: Listener Factory

```python
from abc import ABC, abstractmethod

class IListener(ABC):
    @abstractmethod
    def start(self) -> str:
        pass

class HttpListener(IListener):
    def __init__(self, options: dict):
        self.endpoint = options.get('endpoint', 'localhost:8080')

    def start(self) -> str:
        return f"HTTP Listener started on {self.endpoint}"

class TcpListener(IListener):
    def __init__(self, options: dict):
        self.endpoint = options.get('endpoint', 'localhost:3000')

    def start(self) -> str:
        return f"TCP Listener started on {self.endpoint}"

class ListenerFactory:
    def __init__(self, listeners: list[IListener]):
        self.listeners = listeners

    def start_all(self):
        for listener in self.listeners:
            print(listener.start())

# Setup
services = ServiceProvider()

# Register listeners with options
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    HttpListener({"endpoint": "localhost:8080"}))
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    HttpListener({"endpoint": "localhost:8081"}))
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    TcpListener({"endpoint": "localhost:3000"}))

# Register factory
services.add_singleton(ListenerFactory)

# Use
factory = services.get_service(ListenerFactory)
factory.start_all()
# Output:
# HTTP Listener started on localhost:8080
# HTTP Listener started on localhost:8081
# TCP Listener started on localhost:3000
```

---

## API Reference

### ServiceProvider Methods

#### `get_service(service_type: Type[T]) -> Optional[T]`

Resolves a service:

- If `service_type` is a regular type: Returns first registered implementation
- If `service_type` is `list[Type]`: Returns all registered implementations

**Parameters:**

- `service_type`: The service type to resolve (can be `list[Type]` for multiple)

**Returns:**

- Single instance or list of instances, or `None` if not registered

**Examples:**

```python
# Get single (first) implementation
listener = services.get_service(IListener)

# Get all implementations
all_listeners = services.get_service(list[IListener])
```

#### `add_singleton(service_type, implementation=None, factory=None, instance=None)`

Registers a singleton service. Can be called multiple times for same interface.

**Parameters:**

- `service_type`: The service interface/type
- `implementation`: Concrete implementation class
- `factory`: Factory function
- `instance`: Pre-created instance

**Returns:** `self` (for chaining)

#### `add_scoped(service_type, implementation=None, factory=None)`

Registers a scoped service. Can be called multiple times for same interface.

#### `add_transient(service_type, implementation=None, factory=None)`

Registers a transient service. Can be called multiple times for same interface.

---

## Best Practices

### 1. Registration Order

The first registered implementation is the default:

```python
# First registration becomes default
services.add_singleton(IListener, HttpListener)  # Default
services.add_singleton(IListener, TcpListener)

default = services.get_service(IListener)  # HttpListener
```

### 2. Explicit vs Automatic Injection

Prefer automatic injection over manual resolution:

```python
# ✅ Good: Automatic injection
class ListenerFactory:
    def __init__(self, listeners: list[IListener]):
        self.listeners = listeners

# ❌ Less ideal: Manual resolution
class ListenerFactory:
    def __init__(self, service_provider: IServiceProvider):
        self.listeners = service_provider.get_service(list[IListener])
```

### 3. Type Hints

Always use proper type hints for automatic injection:

```python
# ✅ Good: Proper type hint
def __init__(self, listeners: list[IListener]):
    ...

# ❌ Bad: Missing type hint
def __init__(self, listeners):
    ...
```

### 4. Factory Closures

Be careful with factory closures in loops:

```python
# ❌ Wrong: All factories will use last config
for config in configs:
    services.add_singleton(IListener, factory=lambda sp, **kwargs:
        HttpListener(config))  # All use last config!

# ✅ Correct: Capture config properly
for config in configs:
    services.add_singleton(IListener, factory=lambda sp, cfg=config, **kwargs:
        HttpListener(cfg))  # Each uses its own config
```

---

## Migration Guide

### Before (Single Implementation)

```python
# Old way: Only one implementation
services.add_singleton(IListener, HttpListener)

# Manually create and manage multiple instances
http_listener = HttpListener({"endpoint": "localhost:8080"})
tcp_listener = TcpListener({"endpoint": "localhost:3000"})
listeners = [http_listener, tcp_listener]
```

### After (Multiple Implementations)

```python
# New way: Register multiple
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    HttpListener({"endpoint": "localhost:8080"}))
services.add_singleton(IListener, factory=lambda sp, **kwargs:
    TcpListener({"endpoint": "localhost:3000"}))

# Automatically injected
class ListenerFactory:
    def __init__(self, listeners: list[IListener]):
        self.listeners = listeners  # Auto-injected!
```

### Backward Compatibility

Single resolution still works as before:

```python
# This still returns the first implementation
listener = services.get_service(IListener)  # HttpListener
```

---

## Testing

### Unit Testing with Multiple Implementations

```python
def test_notification_manager():
    # Arrange
    services = ServiceProvider()
    services.add_singleton(INotificationService, EmailNotificationService)
    services.add_singleton(INotificationService, SmsNotificationService)
    services.add_singleton(NotificationManager)

    # Act
    manager = services.get_service(NotificationManager)
    results = manager.broadcast("Test message")

    # Assert
    assert len(results) == 2
    assert "Email:" in results[0]
    assert "SMS:" in results[1]
```

### Testing Individual Implementations

```python
def test_single_listener():
    # Test only HTTP listener
    services = ServiceProvider()
    services.add_singleton(IListener, HttpListener)

    listener = services.get_service(IListener)
    assert isinstance(listener, HttpListener)
```

---

## Performance Considerations

### Caching

- **Singleton**: Created once, cached forever
- **Scoped**: Created once per scope, cached within scope
- **Transient**: Created every time (no caching)

### List Resolution Cost

Resolving `list[Type]` iterates through all registered implementations. For frequently called code with many implementations, consider caching:

```python
class CachedFactory:
    def __init__(self, listeners: list[IListener]):
        self._listeners = listeners  # Cached at construction

    def get_listeners(self) -> list[IListener]:
        return self._listeners  # No resolution cost
```

---

## Troubleshooting

### Empty List Returned

**Problem:**

```python
listeners = services.get_service(list[IListener])
# Returns: []
```

**Solution:** Check that services are registered:

```python
# Ensure registration
services.add_singleton(IListener, HttpListener)
```

### Wrong Type Injected

**Problem:**

```python
class Factory:
    def __init__(self, listeners: list):  # Missing type!
        ...
```

**Solution:** Add proper type hint:

```python
class Factory:
    def __init__(self, listeners: list[IListener]):  # ✅ Correct
        ...
```

### Factory Closure Issues

**Problem:**

```python
for config in configs:
    services.add_singleton(IListener, factory=lambda sp, **kwargs:
        HttpListener(config))  # All use last config
```

**Solution:** Capture config in default parameter:

```python
for config in configs:
    services.add_singleton(IListener, factory=lambda sp, cfg=config, **kwargs:
        HttpListener(cfg))  # ✅ Each uses its own
```

---

## See Also

- [ServiceProvider Documentation](./service-provider.md)
- [Dependency Injection Guide](./dependency-injection.md)
- [Test Examples](../test/di/test_multiple_implementations.py)
- [ListenerFactory Example](../test/di/test_listener_factory_with_multi_di.py)
