# Getting Started with Logger Examples

## Quick Start Guide

All logger examples are now **HTTP servers**. Follow these steps:

### 1. Choose an Example

| Example                            | Port | Focus                   | Difficulty      |
| ---------------------------------- | ---- | ----------------------- | --------------- |
| logger_di_example.py               | 8082 | Basic logger injection  | ⭐ Easy         |
| file_logger_example.py             | 8083 | File logging & rotation | ⭐⭐ Medium     |
| service_provider_logger_example.py | 8084 | ServiceProvider setup   | ⭐⭐ Medium     |
| register_new_logger_example.py     | 8085 | Custom loggers          | ⭐⭐⭐ Advanced |

### 2. Run the Server

```bash
cd test/logger
python logger_di_example.py
```

Output:

```
Starting Logger DI HTTP Server on http://localhost:8082
Available endpoints:
  - GET  /user/login?user_id=123
  - GET  /db/connect
  - POST /order/create?user_id=123&items=item1,item2
  - GET  /order/status?order_id=12345
  - GET  /health

Watch the console for logger output!
```

### 3. Access the Server

Open your browser: http://localhost:8082

You'll see:

- Home page with all available endpoints
- Click any endpoint to test it
- Watch console for log output
- Check `logs/` folder for file logs

### 4. Make Requests

**Browser:**

- Click endpoint links on home page

**curl:**

```bash
curl "http://localhost:8082/user/login?user_id=123"
curl "http://localhost:8082/db/connect"
curl -X POST "http://localhost:8082/order/create?user_id=123&items=item1,item2"
```

**Python requests:**

```python
import requests

response = requests.get('http://localhost:8082/user/login?user_id=123')
print(response.json())
```

### 5. Observe Logger Behavior

**Console Loggers:**

- Watch terminal output
- See colored output (if using ColoredConsoleLogger)
- Different log levels (DEBUG, INFO, WARNING, ERROR)

**File Loggers:**

- Check `logs/` directory
- View log files: `logs/server.log`, `logs/payments.log`, etc.
- Access `/logs/view` endpoint to see logs in browser

## Example Walkthrough

### Example 1: Basic Logger DI (logger_di_example.py)

**Purpose:** Learn how loggers are injected into HTTP handlers

1. Start server: `python logger_di_example.py`
2. Access: http://localhost:8082/user/login?user_id=123
3. Watch console output:
   ```
   2024-12-03 10:30:00 - UserService - INFO - User login attempt | user_id=123
   2024-12-03 10:30:00 - UserService - DEBUG - Request headers: {...}
   ```

**Key Learning:** `ILogger['UserService']` is automatically injected into handler

### Example 2: File Logging (file_logger_example.py)

**Purpose:** Learn file-based logging with rotation

1. Start server: `python file_logger_example.py`
2. Make payment: http://localhost:8083/payment/process?amount=99.99&user_id=123
3. View logs: http://localhost:8083/logs/view
4. Check file: `logs/server.log`

**Key Learning:** Logs persist to file, viewable through web interface

### Example 3: ServiceProvider Setup (service_provider_logger_example.py)

**Purpose:** Learn pre-configured logger registration

1. Start server: `python service_provider_logger_example.py`
2. View config: http://localhost:8084/status
3. See different logger types for different services
4. Make requests to see different logging behaviors

**Key Learning:**

- PaymentService → FileLogger (audit trail)
- UserService → ConsoleLogger (less critical)

### Example 4: Custom Loggers (register_new_logger_example.py)

**Purpose:** Learn to create custom logger implementations

1. Start server: `python register_new_logger_example.py`
2. Create order: http://localhost:8085/order/create?order_id=1001&amount=299.99
3. View JSON logs: http://localhost:8085/logs/json/orders
4. Send notification: http://localhost:8085/notification/send?user_id=123&message=Hello
5. Watch console for colored output

**Key Learning:**

- JsonLogger creates structured JSON logs
- ColoredConsoleLogger adds colors to console
- Easy to extend `ILogger[T]` for custom behavior

## Common Patterns

### Pattern 1: Inject Logger in Handler

```python
@app.restful_handler("order/create")
async def create_order(
    context: edge.RESTfulContext,
    logger: ILogger['OrderService']  # ← Logger injected here
):
    logger.info("Order created", order_id=123)
    return {"status": "success"}
```

### Pattern 2: Register Custom Logger

```python
# Create factory
def create_json_logger(provider, **kwargs):
    generic_type_args = kwargs.get('generic_type_args', [])
    logger_type = generic_type_args[0] if generic_type_args else None
    return JsonLogger(options, logger_type)

# Register with ServiceProvider
sp.add_singleton(ILogger['OrderService'], create_json_logger)

# Use in server
options = {
    "http": "localhost:8085",
    "service_provider": sp
}
app = edge.from_options(options)
```

### Pattern 3: Multiple Log Destinations

```python
# Critical operations → File
sp.add_singleton(ILogger['PaymentService'], create_file_logger)

# General operations → Console
sp.add_singleton(ILogger['CacheService'], create_console_logger)

# Analytics → JSON file
sp.add_singleton(ILogger['AnalyticsService'], create_json_logger)
```

## Testing Tips

1. **Use curl for POST requests:**

   ```bash
   curl -X POST "http://localhost:8083/payment/process?amount=99.99&user_id=123"
   ```

2. **Tail log files in real-time:**

   ```bash
   tail -f logs/server.log
   ```

3. **Run multiple servers simultaneously** (different ports):

   ```bash
   # Terminal 1
   python logger_di_example.py

   # Terminal 2
   python file_logger_example.py

   # Terminal 3
   python service_provider_logger_example.py
   ```

4. **Use Postman or Insomnia** for easier endpoint testing

## Troubleshooting

**Server won't start:**

- Check if port is already in use
- Try changing port in server code
- Kill existing Python processes

**Logs not appearing:**

- Check log level settings
- Verify file permissions for `logs/` directory
- Look for errors in console output

**Import errors:**

- Ensure you're in correct directory
- Check Python path includes bclib
- Verify all dependencies installed

## Next Steps

1. **Modify examples** - Change log formats, levels, destinations
2. **Create your own logger** - Extend `ILogger[T]`
3. **Integrate with your app** - Use patterns in your own HTTP servers
4. **Explore advanced features** - Log filtering, handlers, formatters

## Resources

- [Logger README](README.md) - Detailed documentation
- [BasisCore Edge](../../bclib/edge.py) - Edge framework code
- [ServiceProvider](../di/README.md) - Dependency injection docs
