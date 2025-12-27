# RabbitListener with IRabbitConnection

## Overview

RabbitListener now uses `IRabbitConnection` internally, eliminating code duplication and providing a cleaner architecture.

## Benefits

1. **No Code Duplication**: Connection management is handled by `RabbitConnection`
2. **Consistent Configuration**: Same configuration format for both connection and listener
3. **Easier Testing**: Can mock `IRabbitConnection` for unit tests
4. **Separation of Concerns**: Listener focuses on message consumption, Connection handles connectivity

## Configuration

### appsettings.json

```json
{
  "rabbitmq": {
    "notifications": {
      "url": "amqp://guest:guest@localhost:5672/",
      "exchange": "notifications",
      "exchange_type": "topic",
      "routing_key": "user.*",
      "durable": true,
      "auto_queue": false,
      "queue": "notification_queue"
    },
    "orders": {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "order_queue",
      "durable": true
    }
  }
}
```

### Listener Configuration

```json
{
  "listener": {
    "rabbit_notifications": {
      "type": "rabbit",
      "options": {
        "retry_delay": 60
      }
    }
  }
}
```

## Usage Examples

### Example 1: Exchange-Based Listener with IRabbitConnection

```python
from bclib.connections.rabbit.irabbit_connection import IRabbitConnection
from bclib.listener.rabbit.rabbit_listener import RabbitListener
from bclib.dispatcher.imessage_handler import IMessageHandler
from bclib.logger.ilogger import ILogger

class NotificationHandler:
    def __init__(
        self,
        message_handler: IMessageHandler,
        logger: ILogger['NotificationHandler'],
        rabbit: IRabbitConnection['rabbitmq.notifications']
    ):
        # Create listener with existing connection
        self.listener = RabbitListener(
            message_handler=message_handler,
            logger=logger,
            rabbit_connection=rabbit,
            options={"retry_delay": 30}
        )
```

### Example 2: Queue-Based Listener

```python
class OrderProcessor:
    def __init__(
        self,
        message_handler: IMessageHandler,
        logger: ILogger['OrderProcessor'],
        rabbit: IRabbitConnection['rabbitmq.orders']
    ):
        self.listener = RabbitListener(
            message_handler=message_handler,
            logger=logger,
            rabbit_connection=rabbit,
            options={"retry_delay": 60}
        )
```

### Example 3: Complete Integration

```python
from bclib.edge import Startup
from bclib.connections.rabbit.irabbit_connection import IRabbitConnection
from bclib.listener.rabbit.rabbit_listener import RabbitListener
from bclib.dispatcher.imessage_handler import IMessageHandler
from bclib.logger.ilogger import ILogger

class MessageProcessor:
    def __init__(
        self,
        logger: ILogger['MessageProcessor'],
        rabbit_notifications: IRabbitConnection['rabbitmq.notifications'],
        rabbit_orders: IRabbitConnection['rabbitmq.orders']
    ):
        self.logger = logger
        self.rabbit_notifications = rabbit_notifications
        self.rabbit_orders = rabbit_orders

    async def process_notification(self, message):
        self.logger.info(f"Processing notification: {message}")
        # Process notification logic

    async def process_order(self, message):
        self.logger.info(f"Processing order: {message}")
        # Process order logic

# In your startup configuration
class MyStartup(Startup):
    def configure_listener(self, listener_builder):
        # Register listeners with dependency injection
        listener_builder.add_listener(
            'rabbit_notifications',
            lambda sp: RabbitListener(
                message_handler=sp.get_service(IMessageHandler),
                logger=sp.get_service(ILogger['RabbitListener']),
                rabbit_connection=sp.get_service(IRabbitConnection['rabbitmq.notifications']),
                options={"retry_delay": 30}
            )
        )

        listener_builder.add_listener(
            'rabbit_orders',
            lambda sp: RabbitListener(
                message_handler=sp.get_service(IMessageHandler),
                logger=sp.get_service(ILogger['RabbitListener']),
                rabbit_connection=sp.get_service(IRabbitConnection['rabbitmq.orders']),
                options={"retry_delay": 60}
            )
        )
```

## Key Changes

### Before (Code Duplication)

```python
class RabbitListener(IListener):
    def __init__(self, message_handler, logger, options):
        # 100+ lines of connection setup
        # Duplicate queue/exchange declaration logic
        # Manual connection management
        self.__connection = pika.BlockingConnection(self.__param)
        self.__channel = self.__connection.channel()
        # ... more duplicated code
```

### After (Using IRabbitConnection)

```python
class RabbitListener(IListener):
    def __init__(self, message_handler, logger, rabbit_connection, options):
        # Just store the connection - no duplication!
        self._rabbit = rabbit_connection
        # Focus on listener-specific logic only
```

## Testing

```python
import pytest
from unittest.mock import Mock, MagicMock

def test_rabbit_listener():
    # Mock dependencies
    message_handler = Mock()
    logger = Mock()

    # Mock IRabbitConnection
    mock_rabbit = Mock(spec=IRabbitConnection)
    mock_rabbit.connection = Mock()
    mock_rabbit.connection.params.host = "localhost"
    mock_rabbit.channel = Mock()
    mock_rabbit.is_connected = True

    # Create listener with mocked connection
    listener = RabbitListener(
        message_handler=message_handler,
        logger=logger,
        rabbit_connection=mock_rabbit,
        options={"retry_delay": 5}
    )

    # Verify setup
    assert listener._rabbit == mock_rabbit
    assert listener._host == "localhost"
```

## Migration Guide

If you have existing RabbitListener code without IRabbitConnection:

1. **Add connection to DI container**:

```python
from bclib.connections import add_connection_services
service_collection.add_connection_services()
```

2. **Update listener initialization**:

```python
# Old way
listener = RabbitListener(handler, logger, {
    "url": "amqp://localhost:5672/",
    "queue": "my_queue"
})

# New way
listener = RabbitListener(
    message_handler=handler,
    logger=logger,
    rabbit_connection=rabbit_connection,  # Injected from DI
    options={"retry_delay": 60}
)
```

3. **Move connection config from listener to appsettings**:

```json
{
  "rabbitmq": {
    "my_service": {
      "url": "amqp://localhost:5672/",
      "queue": "my_queue"
    }
  }
}
```

## Summary

✅ **Before**: 200+ lines with duplicated connection logic  
✅ **After**: ~100 lines focused on listening only  
✅ **Result**: 50% code reduction, better maintainability, easier testing
