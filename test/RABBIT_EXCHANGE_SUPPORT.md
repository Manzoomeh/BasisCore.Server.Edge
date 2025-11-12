# RabbitConnection Exchange Support

## Overview

The `RabbitConnection` class has been updated to support **exchange-based publishing** similar to `RabbitSchemaBaseLogger`. This provides more flexibility in RabbitMQ messaging patterns.

## Changes Made

### 1. Configuration Validation

Both classes now enforce the same validation rules:

```python
# ✓ Valid: Queue only
config = {"host": "...", "queue": "my_queue"}

# ✓ Valid: Exchange only
config = {"host": "...", "exchange": "my_exchange"}

# ✗ Invalid: Both queue and exchange
config = {"host": "...", "queue": "my_queue", "exchange": "my_exchange"}
# Raises: "'queue' not acceptable when 'exchange' is set"

# ✗ Invalid: Neither queue nor exchange
config = {"host": "..."}
# Raises: "'exchange' or 'queue' must be set in connection settings"
```

### 2. Enhanced publish() Method

The `publish()` method now accepts an optional `routing_key` parameter:

```python
def publish(self, message: Any, routing_key: Optional[str] = None):
    """Send message to rabbit-mq

    Args:
        message: The message to publish
        routing_key: Optional routing key (required when using exchange, not allowed with queue)
    """
```

### 3. Message Properties

Messages now include proper content properties:

```python
properties = pika.BasicProperties(
    content_type="application/json",
    content_encoding="utf-8"
)
```

### 4. UTF-8 Encoding

JSON serialization now uses `ensure_ascii=False` for proper UTF-8 encoding:

```python
msg_json = json.dumps(message, ensure_ascii=False)
```

## Usage Patterns

### Pattern 1: Direct Queue Publishing (Original Behavior)

```python
from bclib.db_manager.rabbit_connection import RabbitConnection
from bclib.utility import DictEx

config = DictEx({
    "host": "amqp://guest:guest@localhost:5672/",
    "queue": "orders_queue",
    "durable": True
})

with RabbitConnection(config) as conn:
    message = {"order_id": "ORD-001", "status": "pending"}
    conn.publish(message)
    # Published to queue 'orders_queue'
```

### Pattern 2: Exchange with Routing Key (New Feature)

```python
from bclib.db_manager.rabbit_connection import RabbitConnection
from bclib.utility import DictEx

config = DictEx({
    "host": "amqp://guest:guest@localhost:5672/",
    "exchange": "orders_exchange",
    "durable": True
})

with RabbitConnection(config) as conn:
    # Publish to different routing keys
    conn.publish(
        {"order_id": "ORD-001", "status": "created"},
        routing_key="orders.created"
    )

    conn.publish(
        {"order_id": "ORD-002", "status": "completed"},
        routing_key="orders.completed"
    )

    conn.publish(
        {"order_id": "ORD-003", "status": "cancelled"},
        routing_key="orders.cancelled"
    )
```

## Comparison with RabbitSchemaBaseLogger

Both classes now share the same exchange support pattern:

| Feature            | RabbitConnection       | RabbitSchemaBaseLogger |
| ------------------ | ---------------------- | ---------------------- |
| Queue support      | ✅                     | ✅                     |
| Exchange support   | ✅ (NEW)               | ✅                     |
| Routing key        | ✅ (NEW)               | ✅                     |
| Validation         | ✅ (NEW)               | ✅                     |
| UTF-8 encoding     | ✅ (NEW)               | ✅                     |
| Message properties | ✅ (NEW)               | ✅                     |
| Sync/Async         | Sync (context manager) | Async                  |

## Configuration Options

### Common Settings

```python
config = DictEx({
    "host": "amqp://user:pass@host:5672/",  # Required
    "queue": "queue_name",                   # Optional (XOR exchange)
    "exchange": "exchange_name",             # Optional (XOR queue)
    "passive": False,                        # Optional
    "durable": True,                         # Optional
    "exclusive": False,                      # Optional
    "auto_delete": False                     # Optional
})
```

### Validation Rules

1. **Mutual Exclusivity**: Must specify either `queue` OR `exchange`, not both
2. **Routing Key Constraint**: `routing_key` parameter cannot be used when `queue` is configured
3. **Queue Declaration**: Only declared when `queue` is specified (not for exchange mode)

## Migration Guide

### Existing Code (Backward Compatible)

```python
# Old code continues to work unchanged
config = DictEx({
    "host": "amqp://localhost:5672/",
    "queue": "my_queue"
})

with RabbitConnection(config) as conn:
    conn.publish({"data": "value"})
    # Works exactly as before
```

### New Exchange-Based Code

```python
# New exchange-based publishing
config = DictEx({
    "host": "amqp://localhost:5672/",
    "exchange": "my_exchange"  # Changed from queue to exchange
})

with RabbitConnection(config) as conn:
    conn.publish({"data": "value"}, routing_key="my.routing.key")
    # Now supports routing keys
```

## Benefits

### 1. Consistent API

Both `RabbitConnection` and `RabbitSchemaBaseLogger` now have the same configuration pattern, making them easier to use together.

### 2. Flexible Routing

Exchange-based publishing allows for:

- **Topic routing**: Route messages based on patterns (`orders.*`, `*.error`, etc.)
- **Fanout**: Broadcast messages to multiple queues
- **Direct routing**: Route to specific queues by exact match
- **Headers routing**: Route based on message headers

### 3. Better Unicode Support

`ensure_ascii=False` ensures proper handling of non-ASCII characters (Persian, Arabic, emoji, etc.)

### 4. Proper Content Metadata

Messages include content-type and encoding information for better interoperability

## Error Handling

```python
# Invalid: Both queue and exchange
try:
    config = DictEx({
        "host": "...",
        "queue": "q",
        "exchange": "e"
    })
    conn = RabbitConnection(config)
except Exception as e:
    print(e)  # "'queue' not acceptable when 'exchange' is set"

# Invalid: Routing key with queue
try:
    config = DictEx({"host": "...", "queue": "q"})
    with RabbitConnection(config) as conn:
        conn.publish({}, routing_key="key")
except Exception as e:
    print(e)  # "'routing_key' is not acceptable when 'queue' is in settings"

# Invalid: Neither queue nor exchange
try:
    config = DictEx({"host": "..."})
    conn = RabbitConnection(config)
except Exception as e:
    print(e)  # "'exchange' or 'queue' must be set in connection settings"
```

## Examples

See `test/rabbit_exchange_example.py` for complete examples demonstrating:

- Direct queue publishing
- Exchange with routing key
- Configuration validation
- Error cases

## Testing

Run the example:

```bash
python test/rabbit_exchange_example.py
```

This will show configuration guide and validation examples.
