# Logger Examples - HTTP Server Demonstrations

This folder contains HTTP server examples demonstrating the logger system in BasisCore.

## Overview

The logger system provides a generic, type-safe logging interface with dependency injection support. All loggers implement `ILogger[T]` which inherits from Python's standard `logging.Logger`.

**All examples are HTTP servers** - run them and access the endpoints to see loggers in action!

## Built-in Logger Implementations

### 1. ConsoleLogger

Logs to console (stdout) with configurable formatting.

**Usage:**

```python
from bclib.logger import ConsoleLogger, ILogger

logger = ConsoleLogger.create_logger(MyService, {
    'logger': {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
})
```

### 2. FileLogger

Logs to a file with rotation support.

**Usage:**

```python
from bclib.logger import FileLogger, ILogger

logger = FileLogger.create_logger(MyService, {
    'logger': {
        'level': 'INFO',
        'file_path': 'logs/app.log',
        'max_bytes': 1048576,  # 1MB
        'backup_count': 3
    }
})
```

## Example Files

### logger_di_example.py

**HTTP Server on port 8082** - Demonstrates logger dependency injection in HTTP handlers.

**Key concepts:**

- Injecting `ILogger[ServiceName]` directly into HTTP handlers
- Type-safe logger injection
- Different loggers for different endpoints
- Automatic logger creation for each service type

**Run:**

```bash
python test/logger/logger_di_example.py
```

**Endpoints:**

- `GET /user/login?user_id=123` - User login with logger
- `GET /db/connect` - Database connection with logger
- `POST /order/create?user_id=123&items=item1,item2` - Create order
- `GET /order/status?order_id=12345` - Order status
- `GET /health` - Health check

### file_logger_example.py

**HTTP Server on port 8083** - Shows file-based logging with rotation in HTTP context.

**Key concepts:**

- File logging for audit trails
- Log rotation (max_bytes, backup_count)
- Viewing logs through web interface
- Different log files for different purposes

**Run:**

```bash
python test/logger/file_logger_example.py
```

**Endpoints:**

- `POST /payment/process?amount=99.99&user_id=123` - Process payment (logged to file)
- `GET /payment/history?user_id=123` - Payment history
- `POST /email/send?to=user@example.com&subject=Hello` - Send email
- `GET /audit/log?action=login&user=john` - Audit logging
- `GET /logs/view` - View recent log entries

### service_provider_logger_example.py

**HTTP Server on port 8084** - Demonstrates logger registration with ServiceProvider.

**Key concepts:**

- Pre-registering loggers with ServiceProvider
- Different logger types (File/Console) for different services
- Singleton logger instances
- Factory pattern for logger creation
- Automatic dependency injection

**Run:**

```bash
python test/logger/service_provider_logger_example.py
```

**Endpoints:**

- `POST /payment/charge?amount=299.99&user_id=123` - Charge payment (FileLogger)
- `GET /api/request?endpoint=/users&method=GET` - API request (FileLogger)
- `GET /user/profile?user_id=456` - User profile (ConsoleLogger)
- `GET /cache/get?key=user_session_123` - Cache access (ConsoleLogger)
- `GET /status` - View logger configuration

### register_new_logger_example.py

**HTTP Server on port 8085** - Comprehensive guide for creating custom loggers.

**Key concepts:**

- Creating custom logger classes (JsonLogger, ColoredConsoleLogger)
- Extending `ILogger[T]`
- Custom formatters (JSON format, colored output)
- Registering custom loggers with ServiceProvider
- Viewing JSON logs through web interface

**Run:**

```bash
python test/logger/register_new_logger_example.py
```

**Endpoints:**

- `POST /order/create?order_id=1001&amount=299.99` - Create order (JSON log)
- `POST /notification/send?user_id=123&message=Hello` - Send notification (colored console)
- `GET /analytics/track?event=page_view&user_id=456&page=/home` - Track analytics (JSON log)
- `GET /logs/json/orders` - View order JSON logs
- `GET /logs/json/analytics` - View analytics JSON logs

## Quick Start

1. **Run any example server:**

   ```bash
   python test/logger/logger_di_example.py
   ```

2. **Access the home page:**

   - Open http://localhost:8082 (or respective port)
   - See available endpoints and features

3. **Make requests:**

   - Click on endpoint links or use curl/Postman
   - Watch console for logs
   - Check log files in `logs/` directory

4. **Observe logger behavior:**
   - Console output for console loggers
   - File output in `logs/` for file loggers
   - JSON formatted logs for custom JsonLogger
   - Colored output for ColoredConsoleLogger

## Creating a Custom Logger

To create your own logger implementation:

1. **Inherit from ILogger[T]:**

```python
from bclib.logger import ILogger
from typing import TypeVar

T = TypeVar('T')

class MyCustomLogger(ILogger[T]):
    def __init__(self, options: AppOptions, logger_type: Optional[Type[T]] = None):
        self.__logger = self._create_logger(options, logger_type)
```

2. **Implement the create_logger factory method:**

```python
@classmethod
def create_logger(cls, logger_type: Type[T], options: Optional[AppOptions] = None) -> 'MyCustomLogger[T]':
    if options is None:
        options = {}
    return cls(options, logger_type)
```

3. **Create and configure the underlying logging.Logger:**

```python
def _create_logger(self, options: AppOptions, logger_type: Optional[Type[T]]) -> logging.Logger:
    logger_config = options.get('logger', {})
    logger_name = logger_config.get('name', logger_type.__name__ if logger_type else 'MyLogger')

    logger = logging.getLogger(logger_name)
    # Configure handlers, formatters, etc.

    return logger
```

## Registering with ServiceProvider

### Option 1: Using Factory Function

```python
def create_logger_factory(provider, **kwargs):
    generic_type_args = kwargs.get('generic_type_args', [])
    logger_type = generic_type_args[0] if generic_type_args else None
    return MyCustomLogger(options, logger_type)

sp.add_singleton(ILogger[MyService], create_logger_factory)
```

### Option 2: Direct in Server Setup

```python
sp = ServiceProvider()
sp.add_singleton(ILogger['OrderService'], create_json_logger_for_orders)

options = {
    "http": "localhost:8085",
    "service_provider": sp
}

app = edge.from_options(options)
```

## Configuration Options

### Common Logger Options

```python
options = {
    'logger': {
        'name': 'LoggerName',      # Optional, defaults to service class name
        'level': 'DEBUG',           # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}
```

### FileLogger Additional Options

```python
options = {
    'logger': {
        # ... common options ...
        'file_path': 'logs/app.log',       # Required for FileLogger
        'max_bytes': 10485760,              # 10MB, optional
        'backup_count': 5                   # Number of backup files, optional
    }
}
```

## Best Practices

1. **Use Type Parameters in Handlers:**

   ```python
   @app.restful_handler("order/create")
   async def create_order(logger: ILogger['OrderService']):
       logger.info("Order created")
   ```

2. **One Logger Per Service Type:** Different services get different loggers automatically:

   ```python
   sp.add_singleton(ILogger['OrderService'], create_order_logger)
   sp.add_singleton(ILogger['PaymentService'], create_payment_logger)
   ```

3. **Use Appropriate Log Levels:**

   - DEBUG: Detailed information for debugging
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error messages for serious problems
   - CRITICAL: Critical messages for very serious errors

4. **Structured Logging:** Include context in log messages:

   ```python
   logger.info("Order created", order_id=1001, amount=299.99)
   ```

5. **Separate Critical Logs:** Use FileLogger for audit trails and critical operations:

   ```python
   # Payment operations -> File (audit trail)
   sp.add_singleton(ILogger['PaymentService'], create_file_logger)

   # Cache operations -> Console (less critical)
   sp.add_singleton(ILogger['CacheService'], create_console_logger)
   ```

## Port Assignments

- `8082` - logger_di_example.py (Basic DI)
- `8083` - file_logger_example.py (File Logging)
- `8084` - service_provider_logger_example.py (ServiceProvider Registration)
- `8085` - register_new_logger_example.py (Custom Loggers)

## Related Documentation

- [ServiceProvider Documentation](../di/README.md)
- [Generic Types in DI](../di/generic_service_strategy_example.py)
- [BasisCore Edge](../../bclib/edge.py)

## Creating a Custom Logger

To create your own logger implementation:

1. **Inherit from ILogger[T]:**

```python
from bclib.logger import ILogger
from typing import TypeVar

T = TypeVar('T')

class MyCustomLogger(ILogger[T]):
    def __init__(self, options: AppOptions, logger_type: Optional[Type[T]] = None):
        self.__logger = self._create_logger(options, logger_type)
```

2. **Implement the create_logger factory method:**

```python
@classmethod
def create_logger(cls, logger_type: Type[T], options: Optional[AppOptions] = None) -> 'MyCustomLogger[T]':
    if options is None:
        options = {}
    return cls(options, logger_type)
```

3. **Create and configure the underlying logging.Logger:**

```python
def _create_logger(self, options: AppOptions, logger_type: Optional[Type[T]]) -> logging.Logger:
    logger_config = options.get('logger', {})
    logger_name = logger_config.get('name', logger_type.__name__ if logger_type else 'MyLogger')

    logger = logging.getLogger(logger_name)
    # Configure handlers, formatters, etc.

    return logger
```

## Registering with ServiceProvider

### Option 1: Using Factory Function

```python
def create_logger_factory(provider, **kwargs):
    generic_type_args = kwargs.get('generic_type_args', [])
    logger_type = generic_type_args[0] if generic_type_args else None
    return MyCustomLogger(options, logger_type)

sp.add_singleton(ILogger[MyService], create_logger_factory)
```

### Option 2: Using Helper Function

```python
from bclib.logger import register_logger

register_logger(sp, MyCustomLogger, MyService, options)
```

## Configuration Options

### Common Logger Options

```python
options = {
    'logger': {
        'name': 'LoggerName',      # Optional, defaults to service class name
        'level': 'DEBUG',           # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}
```

### FileLogger Additional Options

```python
options = {
    'logger': {
        # ... common options ...
        'file_path': 'logs/app.log',       # Required for FileLogger
        'max_bytes': 10485760,              # 10MB, optional
        'backup_count': 5                   # Number of backup files, optional
    }
}
```

## Best Practices

1. **Use Type Parameters:** Always specify the type when getting a logger:

   ```python
   logger: ILogger[MyService] = sp.get_service(ILogger[MyService])
   ```

2. **One Logger Per Service:** Register a separate logger for each service type:

   ```python
   sp.add_singleton(ILogger[OrderService], create_order_logger)
   sp.add_singleton(ILogger[PaymentService], create_payment_logger)
   ```

3. **Use Appropriate Log Levels:**

   - DEBUG: Detailed information for debugging
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error messages for serious problems
   - CRITICAL: Critical messages for very serious errors

4. **Structured Logging:** Include context in log messages:

   ```python
   logger.info("Order created", order_id=1001, amount=299.99)
   ```

5. **Factory Pattern:** Use the `create_logger` factory method for consistency:
   ```python
   logger = MyLogger.create_logger(MyService, options)
   ```

## Advanced Examples

See `register_new_logger_example.py` for:

- JSON structured logging
- Colored console output
- Custom formatters
- Multiple logger types in one application
- Helper functions for registration

## Related Documentation

- [ServiceProvider Documentation](../di/README.md)
- [Generic Types in DI](../di/generic_service_strategy_example.py)
- [Dependency Injection Basics](../di/simple_di.py)
