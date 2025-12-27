# RabbitMQ Connection - مستندات فارسی 🇮🇷🐰

## 📌 معرفی

سیستم **RabbitMQ Connection** یک راه‌حل مدرن و انعطاف‌پذیر برای مدیریت اتصالات RabbitMQ در BasisCore.Server.Edge است که از الگوی `ILogger<T>` در .NET الهام گرفته شده است.

### ✨ ویژگی‌های کلیدی

- 🎯 **بدون نیاز به وراثت**: مستقیماً از `IRabbitConnection[T]` استفاده کنید
- 🔄 **پشتیبانی Queue و Exchange**: هر دو مد کاری
- ⚡ **Lazy Initialization**: اتصال تنها زمانی ایجاد می‌شود که نیاز باشد
- 🔒 **Type-Safe Configuration**: پیکربندی امن با Generic Types
- 🧪 **قابلیت تست**: راحتی در Mock کردن برای تست‌ها
- 🚀 **Auto Reconnection**: مدیریت خودکار اتصال مجدد در Listener
- 📨 **JSON Serialization**: سریالایز خودکار پیام‌ها

---

## 🚀 شروع سریع

### 1️⃣ ثبت در DI Container

```python
from bclib import edge
from bclib.connections.rabbit import add_rabbitmq_connection

options = {
    "rabbitmq": {
        "tasks": {
            "url": "amqp://guest:guest@localhost:5672/",
            "queue": "task_queue",
            "durable": True
        }
    }
}

app = edge.from_options(options)
```

### 2️⃣ استفاده در Handler

```python
from bclib.connections.rabbit import IRabbitConnection

class TaskHandler:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.tasks']):
        self.rabbit = rabbit

    def process_task(self, task_data: dict):
        # پردازش کار
        result = self.do_work(task_data)

        # ارسال نتیجه به صف
        self.rabbit.publish_to_queue({
            'task_id': task_data['id'],
            'result': result,
            'status': 'completed'
        })
```

---

## 📚 راهنمای استفاده

### 🎯 حالت Queue (مستقیم)

برای ارسال و دریافت پیام‌های مستقیم از یک صف:

```python
from bclib.connections.rabbit import IRabbitConnection

class OrderService:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.orders']):
        self.rabbit = rabbit

    def create_order(self, order_data: dict):
        # ذخیره سفارش در دیتابیس
        order_id = self.save_order(order_data)

        # ارسال به صف پردازش
        self.rabbit.publish_to_queue({
            'order_id': order_id,
            'items': order_data['items'],
            'total': order_data['total']
        })

        return order_id
```

**پیکربندی (Queue Mode):**

```json
{
  "rabbitmq": {
    "orders": {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "order_processing",
      "durable": true
    }
  }
}
```

### 🔄 حالت Exchange (Pub/Sub)

برای ارسال پیام‌ها با Routing Key و Exchange:

```python
from bclib.connections.rabbit import IRabbitConnection

class EventPublisher:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.events']):
        self.rabbit = rabbit

    def publish_user_event(self, event_type: str, user_id: str, data: dict):
        message = {
            'event_type': event_type,
            'user_id': user_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        # ارسال با routing key مشخص
        routing_key = f'user.{event_type}'
        self.rabbit.publish(message, routing_key=routing_key)
```

**پیکربندی (Exchange Mode):**

```json
{
  "rabbitmq": {
    "events": {
      "url": "amqp://guest:guest@localhost:5672/",
      "exchange": "events",
      "exchange_type": "topic",
      "routing_key": "user.*",
      "durable": true
    }
  }
}
```

### 📬 استفاده در Handler (استفاده واقعی)

#### مثال 1: REST API Handler با RabbitMQ

```python
from bclib import edge
from bclib.connections.rabbit import IRabbitConnection
from bclib.connections.mongo import IMongoConnection

class UserHandler:
    def __init__(
        self,
        db: IMongoConnection['database.users'],
        rabbit: IRabbitConnection['rabbitmq.notifications']
    ):
        self.users = db.get_collection('users')
        self.rabbit = rabbit

    async def create_user(self, context: edge.RESTfulContext):
        # دریافت داده از request
        user_data = context.get_request_body()

        # ذخیره کاربر در MongoDB
        result = self.users.insert_one(user_data)
        user_id = str(result.inserted_id)

        # ارسال رویداد ثبت‌نام به RabbitMQ
        self.rabbit.publish({
            'event': 'user.registered',
            'user_id': user_id,
            'email': user_data['email'],
            'name': user_data['name']
        }, routing_key='user.registered')

        # پاسخ به کلاینت
        return {
            'success': True,
            'user_id': user_id,
            'message': 'User created and notification sent'
        }

# ثبت handler
@app.restful_handler(app.url("api/users"))
def handle_users(context: edge.RESTfulContext):
    handler = context.get_service(UserHandler)
    return await handler.create_user(context)
```

#### مثال 2: WebSocket Handler با RabbitMQ

```python
from bclib import edge
from bclib.connections.rabbit import IRabbitConnection

class ChatHandler:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.chat']):
        self.rabbit = rabbit

    async def handle_message(self, context: edge.WebSocketContext):
        message = context.get_request_body()

        # ارسال پیام به صف چت
        self.rabbit.publish({
            'room_id': message['room_id'],
            'user_id': message['user_id'],
            'message': message['text'],
            'timestamp': datetime.now().isoformat()
        }, routing_key=f"chat.room.{message['room_id']}")

        return {'status': 'sent'}

# ثبت WebSocket handler
@app.websocket_handler(app.url("ws/chat"))
def handle_chat(context: edge.WebSocketContext):
    handler = context.get_service(ChatHandler)
    return await handler.handle_message(context)
```

#### مثال 3: RabbitListener Handler (مصرف‌کننده)

```python
from bclib import edge
from bclib.connections.rabbit import IRabbitConnection
from bclib.connections.mongo import IMongoConnection

class NotificationProcessor:
    def __init__(
        self,
        db: IMongoConnection['database.notifications'],
        rabbit: IRabbitConnection['rabbitmq.email_queue']
    ):
        self.notifications = db.get_collection('notifications')
        self.email_rabbit = rabbit

    async def process_notification(self, context: edge.RabbitContext):
        # دریافت پیام از RabbitListener
        message = context.get_request_body()

        # ذخیره در دیتابیس
        notification = {
            'user_id': message['user_id'],
            'type': message['event'],
            'data': message,
            'processed_at': datetime.now(),
            'status': 'processing'
        }
        result = self.notifications.insert_one(notification)

        # اگر نیاز به ارسال ایمیل است
        if message['event'] == 'user.registered':
            self.email_rabbit.publish_to_queue({
                'to': message['email'],
                'subject': 'Welcome!',
                'template': 'welcome',
                'data': message
            })

        # به‌روزرسانی وضعیت
        self.notifications.update_one(
            {'_id': result.inserted_id},
            {'$set': {'status': 'completed'}}
        )

        return {'status': 'processed'}

# ثبت RabbitListener handler
@app.rabbit_handler()
def handle_notifications(context: edge.RabbitContext):
    processor = context.get_service(NotificationProcessor)
    return await processor.process_notification(context)
```

---

## ⚙️ پیکربندی

### 📋 کلیدهای پیکربندی

#### الزامی

- `url`: آدرس اتصال RabbitMQ (مثال: `amqp://guest:guest@localhost:5672/`)

#### انتخاب یکی از دو حالت

**حالت Queue:**

- `queue`: نام صف

**حالت Exchange:**

- `exchange`: نام exchange
- `routing_key`: کلید مسیریابی (اختیاری، پیش‌فرض: `''`)

#### اختیاری

- `exchange_type`: نوع exchange (`topic`, `direct`, `fanout`, `headers`) - پیش‌فرض: `topic`
- `durable`: ماندگاری صف/exchange بعد از restart سرور - پیش‌فرض: `False`
- `exclusive`: صف فقط برای این اتصال - پیش‌فرض: `False`
- `auto_delete`: حذف خودکار وقتی استفاده نمی‌شود - پیش‌فرض: `False`
- `passive`: فقط بررسی وجود، ایجاد نکن - پیش‌فرض: `False`

### 📄 مثال کامل پیکربندی

```json
{
  "rabbitmq": {
    "orders": {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "order_queue",
      "durable": true
    },
    "events": {
      "url": "amqp://guest:guest@localhost:5672/",
      "exchange": "app_events",
      "exchange_type": "topic",
      "routing_key": "events.*",
      "durable": true
    },
    "notifications": {
      "url": "amqp://admin:secret@rabbitmq.example.com:5672/production",
      "exchange": "notifications",
      "exchange_type": "fanout",
      "durable": true
    },
    "tasks": {
      "url": "amqp://guest:guest@localhost:5672/",
      "queue": "background_tasks",
      "durable": true,
      "auto_delete": false
    },
    "logs": {
      "url": "amqp://logger:pass@localhost:5672/logs",
      "exchange": "logs",
      "exchange_type": "topic",
      "routing_key": "app.#",
      "durable": true
    }
  }
}
```

---

## 🎨 سناریوهای پیشرفته

### 1️⃣ Microservices Communication

```python
class OrderService:
    def __init__(
        self,
        db: IMongoConnection['database.orders'],
        inventory_rabbit: IRabbitConnection['rabbitmq.inventory'],
        payment_rabbit: IRabbitConnection['rabbitmq.payments']
    ):
        self.orders = db.get_collection('orders')
        self.inventory = inventory_rabbit
        self.payment = payment_rabbit

    async def create_order(self, order_data: dict):
        # ذخیره سفارش
        order_id = str(self.orders.insert_one(order_data).inserted_id)

        # درخواست به سرویس موجودی
        self.inventory.publish({
            'action': 'reserve',
            'order_id': order_id,
            'items': order_data['items']
        }, routing_key='inventory.reserve')

        # درخواست به سرویس پرداخت
        self.payment.publish({
            'action': 'charge',
            'order_id': order_id,
            'amount': order_data['total']
        }, routing_key='payment.charge')

        return order_id
```

### 2️⃣ Event Sourcing Pattern

```python
class EventStore:
    def __init__(
        self,
        db: IMongoConnection['database.events'],
        rabbit: IRabbitConnection['rabbitmq.events']
    ):
        self.events = db.get_collection('events')
        self.rabbit = rabbit

    async def store_and_publish(self, event: dict):
        # ذخیره event در MongoDB
        event['stored_at'] = datetime.now()
        result = self.events.insert_one(event)
        event['_id'] = str(result.inserted_id)

        # انتشار event در RabbitMQ
        routing_key = f"{event['aggregate_type']}.{event['event_type']}"
        self.rabbit.publish(event, routing_key=routing_key)

        return event
```

### 3️⃣ Background Job Processing

```python
class BackgroundJobService:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.jobs']):
        self.rabbit = rabbit

    def schedule_report(self, report_type: str, params: dict):
        """زمان‌بندی گزارش برای پردازش در پس‌زمینه"""
        job = {
            'type': 'report',
            'report_type': report_type,
            'params': params,
            'scheduled_at': datetime.now().isoformat()
        }
        self.rabbit.publish_to_queue(job)

    def schedule_email_batch(self, recipients: list, template: str):
        """ارسال دسته‌ای ایمیل"""
        job = {
            'type': 'email_batch',
            'recipients': recipients,
            'template': template,
            'scheduled_at': datetime.now().isoformat()
        }
        self.rabbit.publish_to_queue(job)
```

### 4️⃣ استفاده با Context Manager

```python
def send_bulk_notifications():
    from bclib.connections.rabbit import RabbitConnection
    from bclib.options import IOptions

    options: IOptions['notifications'] = {
        'url': 'amqp://guest:guest@localhost:5672/',
        'exchange': 'notifications',
        'exchange_type': 'fanout',
        'durable': True
    }

    # استفاده از context manager
    with RabbitConnection(options) as rabbit:
        for user in get_users():
            rabbit.publish({
                'user_id': user['id'],
                'message': 'System maintenance scheduled'
            })
    # اتصال به صورت خودکار بسته می‌شود
```

---

## 🔗 ادغام با RabbitListener

### نحوه استفاده Connection در Handler های Listener

```python
# پیکربندی
options = {
    "rabbit": [
        {
            "url": "amqp://guest:guest@localhost:5672/",
            "exchange": "events",
            "routing_key": "user.*",
            "exchange_type": "topic"
        }
    ],
    "rabbitmq": {
        "response_queue": {
            "url": "amqp://guest:guest@localhost:5672/",
            "queue": "responses",
            "durable": true
        }
    }
}

# Handler
class EventHandler:
    def __init__(self, response_rabbit: IRabbitConnection['rabbitmq.response_queue']):
        self.response_rabbit = response_rabbit

    async def handle_event(self, context: edge.RabbitContext):
        # دریافت پیام از RabbitListener
        message = context.get_request_body()

        # پردازش
        result = await self.process_event(message)

        # ارسال پاسخ به صف دیگر
        self.response_rabbit.publish_to_queue({
            'original_event': message,
            'result': result,
            'processed_at': datetime.now().isoformat()
        })

        return {'status': 'processed'}
```

---

## 🧪 تست

### Mock کردن برای تست‌ها

```python
from unittest.mock import Mock
from bclib.connections.rabbit import IRabbitConnection

def test_notification_service():
    # ایجاد Mock
    mock_rabbit = Mock(spec=IRabbitConnection)

    # تنظیم رفتار مورد انتظار
    mock_rabbit.publish.return_value = None
    mock_rabbit.is_connected = True

    # استفاده در سرویس
    service = NotificationService(mock_rabbit)
    service.send_notification('user123', 'Hello!')

    # بررسی نتایج
    mock_rabbit.publish.assert_called_once()
    args = mock_rabbit.publish.call_args[0][0]
    assert args['user_id'] == 'user123'
    assert args['message'] == 'Hello!'
```

---

## 🔧 Best Practices

### ✅ انجام دهید

```python
# ✅ استفاده مستقیم از IRabbitConnection
class OrderService:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.orders']):
        self.rabbit = rabbit

# ✅ استفاده از context manager برای عملیات bulk
with RabbitConnection(options) as rabbit:
    for item in items:
        rabbit.publish(item)

# ✅ استفاده از routing key های معنادار
rabbit.publish(event, routing_key='user.registered')

# ✅ استفاده از durable برای پیام‌های مهم
{
    "queue": "critical_tasks",
    "durable": true
}
```

### ❌ انجام ندهید

```python
# ❌ وراثت از RabbitConnection (غیرضروری)
class MyRabbit(RabbitConnection['rabbitmq.tasks']):
    pass

# ❌ ایجاد connection جدید در هر متد
def send_message(message):
    rabbit = RabbitConnection(options)  # ❌ نادرست
    rabbit.publish(message)

# ❌ فراموش کردن بستن اتصال
def process():
    rabbit = RabbitConnection(options)
    rabbit.publish(message)
    # rabbit.close() فراموش شده! ❌

# ❌ استفاده از queue و exchange با هم
{
    "queue": "my_queue",  # ❌ خطا
    "exchange": "my_exchange"  # ❌ خطا
}
```

---

## 🆚 تفاوت با db_manager.RabbitConnection

### قبل (db_manager):

```python
from bclib.db_manager import RabbitConnection

with RabbitConnection(connection_setting) as rabbit:
    rabbit.publish(message)
```

### بعد (connections):

```python
from bclib.connections.rabbit import IRabbitConnection

class MyService:
    def __init__(self, rabbit: IRabbitConnection['rabbitmq.events']):
        self.rabbit = rabbit

    def send_event(self, event: dict):
        self.rabbit.publish(event)
```

### مزایا

1. **Dependency Injection**: استفاده راحت‌تر در DI
2. **Type Safety**: پیکربندی type-safe
3. **No Context Manager**: نیازی به with statement نیست
4. **Lazy Connection**: اتصال فقط زمانی که نیاز است
5. **Multiple Connections**: چندین connection مختلف به راحتی

---

## 💡 نکات مهم

1. **Lazy Initialization**: اتصال تنها زمانی ایجاد می‌شود که از آن استفاده شود
2. **Auto JSON**: پیام‌ها به صورت خودکار به JSON تبدیل می‌شوند
3. **Persistent Messages**: با `durable=true` پیام‌ها بعد از restart حفظ می‌شوند
4. **Routing Patterns**: از `*` و `#` در routing key ها استفاده کنید
5. **Connection Pooling**: pika به صورت خودکار connection pool را مدیریت می‌کند

---

## 📞 پشتیبانی

برای سوالات و مشکلات، لطفاً یک Issue در GitHub ایجاد کنید.

---

**تاریخ به‌روزرسانی**: دسامبر 2025  
**نسخه**: 1.0.0
