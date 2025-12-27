# RabbitMQ Connection Provider - خلاصه پیاده‌سازی

## 🎯 هدف

ایجاد یک RabbitMQ Connection Provider مشابه MongoDB Connection با الگوی `ILogger<T>` که:

- بدون نیاز به وراثت قابل استفاده باشد
- در Handler ها و Service ها قابل تزریق باشد
- هم Queue mode و هم Exchange mode را پشتیبانی کند
- از Lazy Initialization استفاده کند

## 📁 ساختار فایل‌ها

```
bclib/connections/rabbit/
├── __init__.py                      # ثبت در DI Container
├── irabbit_connection.py            # Interface
├── rabbit_connection.py             # Implementation
├── RABBITMQ_CONNECTION_README.md    # مستندات فارسی کامل
└── EXAMPLE_HANDLER_USAGE.py         # مثال کامل استفاده
```

## 🔑 کامپوننت‌های کلیدی

### 1. IRabbitConnection (Interface)

```python
class IRabbitConnection(Generic[T], ABC):
    """RabbitMQ Connection Interface"""

    @property
    @abstractmethod
    def connection(self) -> BlockingConnection: pass

    @property
    @abstractmethod
    def channel(self) -> BlockingChannel: pass

    @abstractmethod
    def publish(self, message: Any, routing_key: Optional[str] = None) -> None: pass

    @abstractmethod
    def publish_to_queue(self, message: Any, queue: Optional[str] = None) -> None: pass

    # ... more methods
```

### 2. RabbitConnection (Implementation)

```python
class RabbitConnection(IRabbitConnection[T]):
    """Concrete implementation with lazy connection"""

    def __init__(self, options: IOptions[T]):
        # Lazy initialization
        self._connection: Optional[BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None
        # Extract and validate options

    @property
    def channel(self) -> BlockingChannel:
        if self._channel is None or self._channel.is_closed:
            self._connect()
        return self._channel

    def publish(self, message: Any, routing_key: Optional[str] = None) -> None:
        # Auto JSON serialization
        message_body = json.dumps(message, ensure_ascii=False)
        # Publish to RabbitMQ
```

### 3. DI Registration

```python
def add_rabbitmq_connection(service_container: IServiceContainer):
    """Register RabbitConnection as IRabbitConnection[T] implementation"""
    def create_rabbit_connection(sp: IServiceProvider, **kwargs):
        # Resolve configuration from key
        # Create and return RabbitConnection

    return service_container.add_scoped(
        IRabbitConnection,
        factory=create_rabbit_connection
    )
```

## 🔧 پیکربندی

### Queue Mode (مستقیم)

```json
{
  "rabbitmq": {
    "tasks": {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "task_queue",
      "durable": true
    }
  }
}
```

### Exchange Mode (Pub/Sub)

```json
{
  "rabbitmq": {
    "events": {
      "url": "amqp://guest:guest@localhost:5672/",
      "exchange": "app_events",
      "exchange_type": "topic",
      "routing_key": "events.*",
      "durable": true
    }
  }
}
```

## 💡 استفاده در Handler

### REST API Handler

```python
class OrderHandler:
    def __init__(
        self,
        db: IMongoConnection['database.orders'],
        rabbit: IRabbitConnection['rabbitmq.events']
    ):
        self.orders = db.get_collection('orders')
        self.rabbit = rabbit

    async def create_order(self, context: edge.RESTfulContext):
        # ذخیره در MongoDB
        order_data = context.get_request_body()
        result = self.orders.insert_one(order_data)

        # ارسال event به RabbitMQ
        self.rabbit.publish({
            'event': 'order.created',
            'order_id': str(result.inserted_id)
        }, routing_key='order.created')

        return {'success': True}
```

### RabbitListener Handler

```python
class EventHandler:
    def __init__(
        self,
        response_rabbit: IRabbitConnection['rabbitmq.responses']
    ):
        self.response_rabbit = response_rabbit

    async def handle_event(self, context: edge.RabbitContext):
        # دریافت از RabbitListener
        message = context.get_request_body()

        # پردازش
        result = self.process(message)

        # ارسال پاسخ به صف دیگر
        self.response_rabbit.publish_to_queue(result)

        return {'status': 'processed'}
```

## ✨ ویژگی‌های کلیدی

### 1. Lazy Initialization

```python
@property
def channel(self) -> BlockingChannel:
    if self._channel is None or self._channel.is_closed:
        self._connect()  # اتصال فقط زمانی که نیاز است
    return self._channel
```

### 2. Auto JSON Serialization

```python
def publish(self, message: Any, routing_key: Optional[str] = None):
    # تبدیل خودکار به JSON
    message_body = json.dumps(message, ensure_ascii=False)
    self.channel.basic_publish(...)
```

### 3. Context Manager Support

```python
with RabbitConnection(options) as rabbit:
    rabbit.publish(message)
# اتصال خودکار بسته می‌شود
```

### 4. Connection Health Check

```python
@property
def is_connected(self) -> bool:
    return (
        self._connection is not None and
        not self._connection.is_closed and
        self._channel is not None and
        self._channel.is_open
    )
```

## 🔄 جریان کار

```
1. DI Container Setup
   ↓
2. add_rabbitmq_connection(services)
   ↓
3. Handler/Service Constructor
   ↓
4. IRabbitConnection['config.key'] injected
   ↓
5. First use: connection created (lazy)
   ↓
6. publish() → auto JSON → RabbitMQ
   ↓
7. RabbitListener receives → Handler processes
   ↓
8. Handler can publish to different queue/exchange
```

## 🆚 مقایسه با روش قدیمی

### قبل (db_manager)

```python
from bclib.db_manager import RabbitConnection

# باید context manager استفاده شود
with RabbitConnection(settings) as rabbit:
    rabbit.publish(message)

# نیاز به تنظیمات دستی
settings = DictEx({...})
```

### بعد (connections)

```python
from bclib.connections.rabbit import IRabbitConnection

# Dependency Injection
class MyService:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.events']):
        self.rabbit = rabbit

    def send_event(self, event: dict):
        self.rabbit.publish(event)  # خیلی ساده‌تر!
```

## 📊 مزایا

1. ✅ **Type Safety**: پیکربندی type-safe با Generic Types
2. ✅ **DI Integration**: تزریق آسان در هر Service/Handler
3. ✅ **Lazy Connection**: اتصال فقط زمانی که نیاز است
4. ✅ **Auto JSON**: سریالایز خودکار پیام‌ها
5. ✅ **Multiple Connections**: چندین connection مختلف به راحتی
6. ✅ **Easy Testing**: Mock کردن راحت برای تست‌ها
7. ✅ **No Context Manager**: نیازی به with statement نیست (اختیاری)

## 🎓 یادگیری از MongoDB Connection

این پیاده‌سازی از همان الگوی MongoDB Connection استفاده می‌کند:

- **Interface**: `IRabbitConnection` شبیه `IMongoConnection`
- **Implementation**: `RabbitConnection` شبیه `MongoConnection`
- **DI Registration**: `add_rabbitmq_connection()` شبیه `add_mongodb_connection()`
- **Usage**: همان الگوی `ILogger<T>`

## 📝 نکات مهم

1. **Mutual Exclusivity**: نمی‌توان هم queue و هم exchange داشت
2. **Routing Key**: در Exchange mode استفاده می‌شود
3. **Durable**: برای پیام‌های مهم true کنید
4. **Exchange Types**: topic, direct, fanout, headers
5. **Connection Pooling**: pika خودکار مدیریت می‌کند

## 🚀 آینده

این ساختار آماده است برای:

- PostgreSQL Connection
- SQL Server Connection
- Redis Connection
- Kafka Connection
- و هر provider دیگری...

---

**نسخه**: 1.0.0  
**تاریخ**: دسامبر 2025
