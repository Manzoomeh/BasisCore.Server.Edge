# MongoDB Connection - مستندات فارسی 🇮🇷

## 📌 معرفی

سیستم **MongoDB Connection** یک راه‌حل مدرن و انعطاف‌پذیر برای مدیریت اتصالات MongoDB در BasisCore.Server.Edge است که از الگوی `ILogger<T>` در .NET الهام گرفته شده است.

### ✨ ویژگی‌های کلیدی

- 🎯 **بدون نیاز به وراثت**: مستقیماً از `IMongoConnection[T]` استفاده کنید
- ⚡ **Lazy Initialization**: اتصال تنها زمانی ایجاد می‌شود که نیاز باشد
- 🔒 **Type-Safe Configuration**: پیکربندی امن با Generic Types
- 🔄 **پشتیبانی Async/Sync**: هم عملیات همزمان و هم ناهمزمان
- 🧪 **قابلیت تست**: راحتی در Mock کردن برای تست‌ها
- 🚀 **Connection Pooling**: مدیریت خودکار Connection Pool

---

## 🚀 شروع سریع

### 1️⃣ ثبت در DI Container

```python
from bclib import edge
from bclib.connections.mongo import add_mongodb_connection

options = {
    "database": {
        "users": {
            "connection_string": "mongodb://localhost:27017",
            "database_name": "myapp_users"
        }
    }
}

app = edge.from_options(options)
```

### 2️⃣ استفاده در سرویس‌ها

```python
from bclib.connections.mongo import IMongoConnection

class UserService:
    def __init__(self, db: IMongoConnection['database.users']):
        self.db = db
        self.users = db.get_collection('users')

    def get_user(self, user_id: str):
        return self.users.find_one({'_id': user_id})
```

---

## 📚 راهنمای استفاده

### 🎯 روش پیشنهادی: استفاده مستقیم (ILogger Style)

این روش **ساده‌ترین و پیشنهادی** است:

```python
from bclib.connections.mongo import IMongoConnection

class ProductService:
    def __init__(self, db: IMongoConnection['database.products']):
        self.db = db
        # دسترسی مستقیم به collection ها
        self.products = db.get_collection('products')
        self.categories = db.get_collection('categories')

    def get_product(self, product_id: str):
        return self.products.find_one({'_id': product_id})

    def get_all_products(self):
        return list(self.products.find())
```

### 🔄 عملیات Async

```python
class AsyncUserService:
    def __init__(self, db: IMongoConnection['database.users']):
        self.db = db
        self.users = db.get_async_collection('users')

    async def get_user(self, user_id: str):
        return await self.users.find_one({'_id': user_id})

    async def create_user(self, user_data: dict):
        result = await self.users.insert_one(user_data)
        return result.inserted_id
```

### 🗂️ مدیریت Collection ها

```python
class OrderService:
    def __init__(self, db: IMongoConnection['database.orders']):
        self.db = db

    def setup_collections(self):
        # بررسی وجود collection
        if not self.db.collection_exists('orders'):
            # ایجاد collection جدید
            self.db.create_collection('orders')

        # دسترسی به collection
        orders = self.db.get_collection('orders')
        return orders

    def cleanup(self):
        # حذف collection (احتیاط: غیرقابل بازگشت!)
        self.db.drop_collection('temp_orders')
```

---

## ⚙️ پیکربندی

### 📋 کلیدهای پیکربندی

#### الزامی:

- `connection_string`: رشته اتصال MongoDB
- `database_name`: نام دیتابیس

#### اختیاری:

- `timeout`: زمان timeout اتصال به میلی‌ثانیه (پیش‌فرض: 5000)
- `max_pool_size`: حداکثر اندازه Connection Pool (پیش‌فرض: 100)
- `min_pool_size`: حداقل اندازه Connection Pool (پیش‌فرض: 0)
- `server_selection_timeout`: زمان timeout انتخاب سرور (پیش‌فرض: 30000)

### 📄 مثال کامل پیکربندی (appsettings.json)

```json
{
  "database": {
    "users": {
      "connection_string": "mongodb://localhost:27017",
      "database_name": "myapp_users",
      "timeout": 5000,
      "max_pool_size": 100,
      "min_pool_size": 10,
      "server_selection_timeout": 30000
    },
    "products": {
      "connection_string": "mongodb://localhost:27017",
      "database_name": "myapp_products",
      "timeout": 3000,
      "max_pool_size": 50
    },
    "logs": {
      "connection_string": "mongodb://log-server:27017",
      "database_name": "application_logs",
      "max_pool_size": 20
    }
  }
}
```

---

## 🎨 سناریوهای استفاده

### 1️⃣ CRUD عملیات ساده

```python
class BlogService:
    def __init__(self, db: IMongoConnection['database.blog']):
        self.posts = db.get_collection('posts')

    def create_post(self, title: str, content: str):
        post = {
            'title': title,
            'content': content,
            'created_at': datetime.now()
        }
        result = self.posts.insert_one(post)
        return result.inserted_id

    def get_post(self, post_id):
        return self.posts.find_one({'_id': post_id})

    def update_post(self, post_id, updates: dict):
        self.posts.update_one(
            {'_id': post_id},
            {'$set': updates}
        )

    def delete_post(self, post_id):
        self.posts.delete_one({'_id': post_id})
```

### 2️⃣ کار با چند Collection

```python
class ECommerceService:
    def __init__(self, db: IMongoConnection['database.shop']):
        self.products = db.get_collection('products')
        self.orders = db.get_collection('orders')
        self.customers = db.get_collection('customers')

    def place_order(self, customer_id: str, product_ids: list):
        # بررسی موجودی محصولات
        products = list(self.products.find({
            '_id': {'$in': product_ids}
        }))

        # ایجاد سفارش
        order = {
            'customer_id': customer_id,
            'products': products,
            'created_at': datetime.now()
        }
        result = self.orders.insert_one(order)

        # به‌روزرسانی تاریخچه مشتری
        self.customers.update_one(
            {'_id': customer_id},
            {'$push': {'orders': result.inserted_id}}
        )

        return result.inserted_id
```

### 3️⃣ عملیات Async پیشرفته

```python
class AsyncAnalyticsService:
    def __init__(self, db: IMongoConnection['database.analytics']):
        self.events = db.get_async_collection('events')

    async def log_event(self, event_type: str, data: dict):
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now()
        }
        await self.events.insert_one(event)

    async def get_user_events(self, user_id: str, limit: int = 100):
        cursor = self.events.find(
            {'data.user_id': user_id}
        ).sort('timestamp', -1).limit(limit)

        return await cursor.to_list(length=limit)

    async def aggregate_stats(self, start_date, end_date):
        pipeline = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1}
                }
            }
        ]

        cursor = self.events.aggregate(pipeline)
        return await cursor.to_list(length=None)
```

### 4️⃣ Context Manager Usage

```python
def export_data():
    from bclib.connections.mongo import MongoConnection
    from bclib.options import IOptions

    options: IOptions['export'] = {
        'connection_string': 'mongodb://localhost:27017',
        'database_name': 'export_db'
    }

    # استفاده از context manager برای مدیریت خودکار اتصال
    with MongoConnection(options) as db:
        data = db.get_collection('export_data')
        records = list(data.find())
        return records
    # اتصال به صورت خودکار بسته می‌شود
```

---

## 🧪 تست

### Mock کردن برای تست‌ها

```python
from unittest.mock import Mock
from bclib.connections.mongo import IMongoConnection

def test_user_service():
    # ایجاد Mock
    mock_db = Mock(spec=IMongoConnection)
    mock_collection = Mock()
    mock_db.get_collection.return_value = mock_collection

    # تنظیم رفتار مورد انتظار
    mock_collection.find_one.return_value = {
        '_id': '123',
        'name': 'Test User'
    }

    # استفاده در سرویس
    service = UserService(mock_db)
    user = service.get_user('123')

    # بررسی نتایج
    assert user['name'] == 'Test User'
    mock_collection.find_one.assert_called_once_with({'_id': '123'})
```

---

## 🔧 Best Practices

### ✅ انجام دهید:

```python
# ✅ استفاده مستقیم از IMongoConnection
class UserService:
    def __init__(self, db: IMongoConnection['database.users']):
        self.users = db.get_collection('users')

# ✅ Cache کردن collection reference
class ProductService:
    def __init__(self, db: IMongoConnection['database.products']):
        self.db = db
        self.products = db.get_collection('products')
        self.categories = db.get_collection('categories')

# ✅ استفاده از async برای عملیات سنگین
class AnalyticsService:
    def __init__(self, db: IMongoConnection['database.analytics']):
        self.events = db.get_async_collection('events')
```

### ❌ انجام ندهید:

```python
# ❌ وراثت از MongoConnection (غیرضروری)
class UserConnection(MongoConnection['database.users']):
    pass

# ❌ ایجاد connection جدید در هر متد
def get_user(user_id):
    db = MongoConnection(options)  # ❌ نادرست
    return db.get_collection('users').find_one({'_id': user_id})

# ❌ فراموش کردن بستن اتصال در استفاده مستقیم
def process_data():
    db = MongoConnection(options)
    # عملیات...
    # db.close() فراموش شده! ❌
```

---

## 🆚 مقایسه با روش قدیمی (DbContext)

### قبل (DbContext):

```python
from bclib.db_context.mongo import IMongoDbContext

class UserService:
    def __init__(self, db: IMongoDbContext['database.users']):
        self.db = db
```

### بعد (Connection):

```python
from bclib.connections.mongo import IMongoConnection

class UserService:
    def __init__(self, db: IMongoConnection['database.users']):
        self.db = db
```

### مزایای Connection نسبت به DbContext:

1. **مفهوم واضح‌تر**: Connection به جای Context
2. **سازگاری بهتر**: آماده برای پشتیبانی از provider های مختلف
3. **معماری بهتر**: جداسازی واضح‌تر مسئولیت‌ها

---

## 🔜 آینده

### Provider های آینده:

- 🐘 **PostgreSQL Connection**
- 🗄️ **SQL Server Connection**
- 🔥 **Redis Connection**
- 🐰 **RabbitMQ Connection**

---

## 💡 نکات مهم

1. **Lazy Initialization**: اتصال تنها زمانی ایجاد می‌شود که از آن استفاده شود
2. **Connection Pooling**: MongoDB driver به صورت خودکار connection pool را مدیریت می‌کند
3. **Thread Safety**: MongoClient thread-safe است
4. **Async Support**: برای عملیات I/O سنگین از async استفاده کنید

---

## 📞 پشتیبانی

برای سوالات و مشکلات، لطفاً یک Issue در GitHub ایجاد کنید.

---

**تاریخ به‌روزرسانی**: دسامبر 2025  
**نسخه**: 2.0.0 (Connection-based)
