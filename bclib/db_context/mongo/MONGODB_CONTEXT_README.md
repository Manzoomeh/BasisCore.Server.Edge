# MongoDB Context Architecture

معماری مدرن و قدرتمند برای مدیریت MongoDB در BasisCore، الهام گرفته از **ILogger<T>** pattern در ASP.NET Core.

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها)
- [نصب](#نصب)
- [شروع سریع](#شروع-سریع)
- [مفاهیم پایه](#مفاهیم-پایه)
- [راهنمای استفاده](#راهنمای-استفاده)
- [پیکربندی](#پیکربندی)
- [الگوهای پیشرفته](#الگوهای-پیشرفته)
- [تست](#تست)

## ✨ ویژگی‌ها

- **No Inheritance Required**: مثل ILogger، نیازی به ارث‌بری ندارید!
- **Sync & Async Support**: پشتیبانی همزمان از MongoClient (sync) و AsyncMongoClient (async)
- **Type-Safe Configuration**: استفاده از Generic Types برای تزریق تنظیمات type-safe
- **Direct Injection**: استفاده مستقیم از `IMongoDbContext[TConfig]` در constructor
- **Lazy Initialization**: اتصال به دیتابیس (sync و async) فقط هنگام نیاز برقرار می‌شود
- **Context Manager Support**: مدیریت خودکار اتصالات با استفاده از `with` statement
- **Dependency Injection Ready**: کاملاً سازگار با سیستم DI موجود در BasisCore
- **Easy Testing**: به راحتی قابل Mock کردن برای تست
- **Configuration from IOptions**: پیکربندی از طریق سیستم Options مشابه ASP.NET Core
- **Connection Pooling**: پشتیبانی کامل از connection pooling برای بهینه‌سازی عملکرد

## 📦 نصب

نیازمندی:

```bash
pip install pymongo
```

## 🚀 شروع سریع

### روش جدید (پیشنهادی - ILogger Style) 🎯

**نیازی به ساختن کلاس Context ندارید!**

```python
from bclib.db_context.mongo import IMongoDbContext
from bclib.options import IOptions

# مستقیماً در سرویس استفاده کنید
class UserService:
    def __init__(self, db: IMongoDbContext['database.users']):
        self.db = db
        # Cache کردن collections (sync)
        self.users = db.get_collection('users')
        self.profiles = db.get_collection('profiles')

    def create_user(self, user_data: dict) -> str:
        """Sync version"""
        result = self.users.insert_one(user_data)
        return str(result.inserted_id)

    def get_user(self, user_id: str) -> dict:
        """Sync version"""
        return self.users.find_one({'_id': user_id})

# استفاده از Async
class AsyncUserService:
    def __init__(self, db: IMongoDbContext['database.users']):
        self.db = db
        # Cache کردن collections (async)
        self.users = db.get_async_collection('users')
        self.profiles = db.get_async_collection('profiles')

    async def create_user(self, user_data: dict) -> str:
        """Async version"""
        result = await self.users.insert_one(user_data)
        return str(result.inserted_id)

    async def get_user(self, user_id: str) -> dict:
        """Async version"""
        return await self.users.find_one({'_id': user_id})
```

### پیکربندی در فایل تنظیمات

```json
{
  "database": {
    "users": {
      "connection_string": "mongodb://localhost:27017",
      "database_name": "users_db",
      "max_pool_size": 100
    }
  }
}
```

### ثبت در DI Container

```python
from bclib.db_context.mongo import add_mongodb_default_context

def configure_services(services):
    # روش 1: استفاده از add_mongodb_default_context (ساده‌ترین و پیشنهادی) ⭐
    add_mongodb_default_context(services)

    # این یک خط کد، تمام IMongoDbContext[T] را برای همه configuration ها فعال می‌کند!
    # پشتیبانی از هر دو sync و async
    # حالا می‌توانید در هر سرویسی از IMongoDbContext['database.xxx'] استفاده کنید

    # ثبت سرویس‌های وابسته
    services.add_scoped(UserService)
    services.add_scoped(AsyncUserService)
```

#### روش Manual (اختیاری - معمولاً نیاز نیست)

```python
from bclib.db_context.mongo import IMongoDbContext, MongoDbContext

def configure_services_manual(services):
    # روش 2: ثبت manual (فقط در صورت نیاز به کنترل بیشتر)
    services.add_scoped(
        IMongoDbContext['database.users'],
        factory=lambda sp: MongoDbContext(sp.get(IOptions['database.users']))
    )

    services.add_scoped(UserService)
```

## 💡 مفاهیم پایه

### ILogger Style Pattern

مشابه `ILogger<T>` در ASP.NET Core، از `IMongoDbContext[TConfig]` استفاده می‌کنیم:

```python
# ❌ قدیمی: نیاز به ارث‌بری
class UserDbContext(MongoDbContext['database.users']):
    def __init__(self, options):
        super().__init__(options)

# ✅ جدید: استفاده مستقیم
class UserService:
    def __init__(self, db: IMongoDbContext['database.users']):
        self.db = db
```

### Generic Type Parameter

پارامتر Generic مشخص می‌کند که کانفیگ از کجای فایل تنظیمات خوانده شود:

```python
# از 'database.users' در کانفیگ استفاده می‌کند
class UserDbContext(MongoDbContext['database.users']):
    ...

# از 'database.products' در کانفیگ استفاده می‌کند
class ProductDbContext(MongoDbContext['database.products']):
    ...

# از 'logging.mongodb' در کانفیگ استفاده می‌کند
class LogDbContext(MongoDbContext['logging.mongodb']):
    ...
```

### IOptions Pattern

مشابه ASP.NET Core، تنظیمات از طریق `IOptions<T>` تزریق می‌شوند:

```python
def __init__(self, options: IOptions['database.users']):
    super().__init__(options)
```

### Lazy Initialization

اتصال به دیتابیس (sync و async) تا زمان اولین استفاده برقرار نمی‌شود:

```python
# هنوز اتصالی برقرار نشده
context = UserDbContext(options)

# اکنون sync client برقرار می‌شود
users = context.users.find()

# async client مستقل است و lazy initialization دارد
async_users = context.get_async_collection('users')
result = await async_users.find_one({})
```

### Sync vs Async Collections

```python
class DualModeService:
    def __init__(self, db: IMongoDbContext['database.users']):
        self.db = db

    # Sync operations
    def get_user_sync(self, user_id: str):
        users = self.db.get_collection('users')
        return users.find_one({'_id': user_id})

    # Async operations
    async def get_user_async(self, user_id: str):
        users = self.db.get_async_collection('users')
        return await users.find_one({'_id': user_id})
```

## 📖 راهنمای استفاده

### مثال کامل: سیستم مدیریت کاربر

```python
from bclib.db_manager.mongo_db_context import MongoDbContext
from bclib.options.ioptions import IOptions
from typing import Optional, List, Dict, Any
from datetime import datetime

# 1. تعریف Context
class UserDbContext(MongoDbContext['database.users']):
    def __init__(self, options: IOptions['database.users']):
        super().__init__(options)

    @property
    def users(self):
        return self.get_collection('users')

    @property
    def sessions(self):
        return self.get_collection('sessions')

    @property
    def audit_logs(self):
        return self.get_collection('audit_logs')

# 2. تعریف Service Layer
class UserService:
    def __init__(self, db: UserDbContext):
        self.db = db

    async def register_user(self, email: str, password: str, name: str) -> str:
        """ثبت نام کاربر جدید"""
        user = {
            'email': email,
            'password': password,  # در واقعیت باید hash شود
            'name': name,
            'created_at': datetime.utcnow(),
            'is_active': True
        }

        result = self.db.users.insert_one(user)

        # ثبت در لاگ
        self.db.audit_logs.insert_one({
            'action': 'user_registered',
            'user_id': result.inserted_id,
            'timestamp': datetime.utcnow()
        })

        return str(result.inserted_id)

    async def authenticate(self, email: str, password: str) -> Optional[str]:
        """احراز هویت کاربر"""
        user = self.db.users.find_one({
            'email': email,
            'password': password,
            'is_active': True
        })

        if user:
            # ایجاد session
            session = {
                'user_id': user['_id'],
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=24)
            }
            result = self.db.sessions.insert_one(session)
            return str(result.inserted_id)

        return None

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """دریافت پروفایل کاربر"""
        return self.db.users.find_one(
            {'_id': user_id},
            {'password': 0}  # پسورد را نمایش نده
        )

    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        """جستجوی کاربران"""
        return list(self.db.users.find(
            {
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'email': {'$regex': query, '$options': 'i'}}
                ]
            },
            {'password': 0}
        ).limit(50))

    async def deactivate_user(self, user_id: str):
        """غیرفعال کردن کاربر"""
        self.db.users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'is_active': False,
                    'deactivated_at': datetime.utcnow()
                }
            }
        )

        # حذف session های فعال
        self.db.sessions.delete_many({'user_id': user_id})

# 3. ثبت در DI
def register_services(services):
    services.add_scoped(UserDbContext)
    services.add_scoped(UserService)

# 4. استفاده در Application
async def main():
    # فرض: service_provider از DI container دریافت شده
    user_service = service_provider.get(UserService)

    # ثبت نام کاربر جدید
    user_id = await user_service.register_user(
        email='test@example.com',
        password='secure_password',
        name='Test User'
    )

    # احراز هویت
    session_id = await user_service.authenticate(
        email='test@example.com',
        password='secure_password'
    )

    # دریافت پروفایل
    profile = await user_service.get_user_profile(user_id)
    print(f"User: {profile['name']}")
```

### استفاده با Context Manager

```python
# مدیریت خودکار اتصال
with UserDbContext(options) as db:
    users = list(db.users.find().limit(10))
    # اتصال به صورت خودکار بسته می‌شود
```

### چند Context همزمان

```python
class SyncService:
    def __init__(self,
                 user_db: UserDbContext,
                 product_db: ProductDbContext,
                 log_db: LogDbContext):
        self.user_db = user_db
        self.product_db = product_db
        self.log_db = log_db

    async def sync_data(self):
        """همگام‌سازی داده بین دیتابیس‌های مختلف"""
        users = list(self.user_db.users.find())

        for user in users:
            # پردازش...
            self.log_db.sync_logs.insert_one({
                'user_id': user['_id'],
                'synced_at': datetime.utcnow()
            })
```

## ⚙️ پیکربندی

### تنظیمات پایه (الزامی)

```json
{
  "database": {
    "mydb": {
      "connection_string": "mongodb://localhost:27017",
      "database_name": "my_database"
    }
  }
}
```

### تنظیمات پیشرفته

```json
{
  "database": {
    "mydb": {
      "connection_string": "mongodb://user:pass@host:27017/?authSource=admin",
      "database_name": "my_database",
      "timeout": 5000,
      "max_pool_size": 100,
      "min_pool_size": 10,
      "server_selection_timeout": 30000
    }
  }
}
```

### تنظیمات برای MongoDB Atlas

```json
{
  "database": {
    "production": {
      "connection_string": "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority",
      "database_name": "prod_db",
      "max_pool_size": 50,
      "server_selection_timeout": 10000
    }
  }
}
```

### تنظیمات Replica Set

```json
{
  "database": {
    "clustered": {
      "connection_string": "mongodb://host1:27017,host2:27017,host3:27017/?replicaSet=myRepl",
      "database_name": "cluster_db",
      "max_pool_size": 200
    }
  }
}
```

## 🔥 الگوهای پیشرفته

### Repository Pattern

```python
class BaseRepository:
    def __init__(self, context: MongoDbContext, collection_name: str):
        self.collection = context.get_collection(collection_name)

    def find_by_id(self, doc_id: str):
        return self.collection.find_one({'_id': doc_id})

    def find_all(self, filter_query=None):
        return list(self.collection.find(filter_query or {}))

    def insert(self, document: dict) -> str:
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def update(self, doc_id: str, updates: dict) -> bool:
        result = self.collection.update_one(
            {'_id': doc_id},
            {'$set': updates}
        )
        return result.modified_count > 0

    def delete(self, doc_id: str) -> bool:
        result = self.collection.delete_one({'_id': doc_id})
        return result.deleted_count > 0

class UserRepository(BaseRepository):
    def __init__(self, context: UserDbContext):
        super().__init__(context, 'users')

    def find_by_email(self, email: str):
        return self.collection.find_one({'email': email})

    def find_active_users(self):
        return self.find_all({'is_active': True})
```

### Multi-Tenant Pattern

```python
class TenantDbContext(MongoDbContext['database.multitenant']):
    def __init__(self, options: IOptions['database.multitenant']):
        super().__init__(options)

    def get_tenant_collection(self, tenant_id: str, collection_name: str):
        """دریافت collection مخصوص tenant"""
        full_name = f"tenant_{tenant_id}_{collection_name}"
        return self.get_collection(full_name)

    def initialize_tenant(self, tenant_id: str):
        """ایجاد collection های لازم برای tenant جدید"""
        collections = ['users', 'orders', 'products']
        for coll in collections:
            name = f"tenant_{tenant_id}_{coll}"
            if not self.collection_exists(name):
                self.create_collection(name)

class TenantService:
    def __init__(self, db: TenantDbContext):
        self.db = db

    async def get_tenant_users(self, tenant_id: str):
        users_coll = self.db.get_tenant_collection(tenant_id, 'users')
        return list(users_coll.find())
```

### Capped Collections برای Logging

```python
class LogDbContext(MongoDbContext['database.logs']):
    def __init__(self, options: IOptions['database.logs']):
        super().__init__(options)
        self._ensure_capped_collections()

    def _ensure_capped_collections(self):
        """ایجاد capped collection ها برای لاگ"""
        if not self.collection_exists('app_logs'):
            self.create_collection(
                'app_logs',
                capped=True,
                size=100_000_000,  # 100MB
                max=10000          # حداکثر 10000 سند
            )

    @property
    def app_logs(self):
        return self.get_collection('app_logs')
```

### Aggregation Pipeline

```python
class AnalyticsService:
    def __init__(self, db: UserDbContext):
        self.db = db

    async def get_user_statistics(self):
        """آمار کاربران با استفاده از aggregation"""
        pipeline = [
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            }
        ]

        return list(self.db.users.aggregate(pipeline))

    async def get_active_users_by_date(self):
        """کاربران فعال بر اساس تاریخ"""
        pipeline = [
            {
                '$match': {'is_active': True}
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$created_at'
                        }
                    },
                    'count': {'$sum': 1}
                }
            }
        ]

        return list(self.db.users.aggregate(pipeline))
```

## 🧪 تست

### Unit Test با Mock

```python
import unittest
from unittest.mock import Mock, patch

class TestUserService(unittest.TestCase):
    @patch('bclib.db_manager.mongo_db_context.MongoClient')
    def test_create_user(self, mock_client):
        # Setup
        mock_collection = Mock()
        mock_collection.insert_one.return_value.inserted_id = 'user_123'

        context = UserDbContext(test_options)
        context._database = Mock()
        context._database.__getitem__.return_value = mock_collection

        service = UserService(context)

        # Test
        user_id = service.create_user({'name': 'Test'})

        # Assert
        self.assertEqual(user_id, 'user_123')
        mock_collection.insert_one.assert_called_once()
```

### Integration Test

```python
class TestUserDbContextIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """راه‌اندازی برای تست‌های integration"""
        cls.options = {
            'connection_string': 'mongodb://localhost:27017',
            'database_name': 'test_db'
        }

    def test_crud_operations(self):
        """تست عملیات CRUD"""
        with UserDbContext(self.options) as db:
            # Create
            result = db.users.insert_one({'name': 'Test User'})
            user_id = result.inserted_id

            # Read
            user = db.users.find_one({'_id': user_id})
            self.assertEqual(user['name'], 'Test User')

            # Update
            db.users.update_one(
                {'_id': user_id},
                {'$set': {'name': 'Updated User'}}
            )

            # Delete
            db.users.delete_one({'_id': user_id})
```

## 📚 مقایسه با روش قبلی

### روش قدیمی (Singleton)

```python
# مشکلات:
# - Singleton باعث مشکل در testing می‌شود
# - پیکربندی سخت‌افزاری (hard-coded)
# - عدم پشتیبانی از DI
# - مدیریت سخت چند دیتابیس

class MongoDb(metaclass=SingletonMeta):
    def __init__(self, connection_string: str):
        self.client = pymongo.MongoClient(connection_string)
```

### روش جدید (DbContext)

```python
# مزایا:
# ✅ Type-safe configuration
# ✅ سازگار با DI
# ✅ قابل test با mock
# ✅ مدیریت آسان چند دیتابیس
# ✅ Lazy initialization
# ✅ Context manager support

class UserDbContext(MongoDbContext['database.users']):
    def __init__(self, options: IOptions['database.users']):
        super().__init__(options)
```

## 🎯 Best Practices

1. **همیشه از Context Manager استفاده کنید**

   ```python
   with UserDbContext(options) as db:
       # کار با دیتابیس
       pass
   # اتصال خودکار بسته می‌شود
   ```

2. **Property ها را برای Collection های مکرر تعریف کنید**

   ```python
   @property
   def users(self):
       return self.get_collection('users')
   ```

3. **Context را Scoped ثبت کنید نه Singleton**

   ```python
   services.add_scoped(UserDbContext)  # ✅
   services.add_singleton(UserDbContext)  # ❌
   ```

4. **پسورد را در کانفیگ hard-code نکنید**

   ```python
   # ❌ Bad
   "connection_string": "mongodb://user:pass123@host"

   # ✅ Good - استفاده از environment variable
   "connection_string": "${MONGO_CONNECTION_STRING}"
   ```

5. **برای لاگ از Capped Collection استفاده کنید**

6. **Index ها را مدیریت کنید**
   ```python
   def _ensure_indexes(self):
       self.users.create_index('email', unique=True)
       self.users.create_index([('created_at', -1)])
   ```

## 🤝 مشارکت

برای گزارش مشکل یا پیشنهاد بهبود، لطفاً Issue ایجاد کنید.

## 📝 License

مطابق با لایسنس BasisCore.Server.Edge

---

**ساخته شده با ❤️ برای BasisCore**
