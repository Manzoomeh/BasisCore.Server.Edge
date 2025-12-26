# تغییرات Refactoring: از DbContext به Connection

## 📋 خلاصه تغییرات

این refactoring مفهوم `DbContext` را به `Connection` تبدیل کرده است تا معماری واضح‌تر و قابل توسعه‌تری برای مدیریت اتصالات پایگاه داده فراهم شود.

## 🔄 تغییرات ساختاری

### پوشه‌ها

```
قبل:
bclib/
  └── db_context/
      ├── __init__.py
      └── mongo/
          ├── __init__.py
          ├── imongo_db_context.py
          ├── mongo_db_context.py
          └── MONGODB_CONTEXT_README.md

بعد:
bclib/
  └── connections/
      ├── __init__.py
      └── mongo/
          ├── __init__.py
          ├── imongo_connection.py
          ├── mongo_connection.py
          └── MONGODB_CONNECTION_README.md
```

### فایل‌ها

| فایل قدیمی                                   | فایل جدید                                        |
| -------------------------------------------- | ------------------------------------------------ |
| `db_context/__init__.py`                     | `connections/__init__.py`                        |
| `db_context/mongo/__init__.py`               | `connections/mongo/__init__.py`                  |
| `db_context/mongo/imongo_db_context.py`      | `connections/mongo/imongo_connection.py`         |
| `db_context/mongo/mongo_db_context.py`       | `connections/mongo/mongo_connection.py`          |
| `db_context/mongo/MONGODB_CONTEXT_README.md` | `connections/mongo/MONGODB_CONNECTION_README.md` |

## 📝 تغییرات کد

### کلاس‌ها و Interface ها

| قبل               | بعد                |
| ----------------- | ------------------ |
| `IMongoDbContext` | `IMongoConnection` |
| `MongoDbContext`  | `MongoConnection`  |

### توابع

| قبل                             | بعد                         |
| ------------------------------- | --------------------------- |
| `add_db_context_services()`     | `add_connection_services()` |
| `add_mongodb_default_context()` | `add_mongodb_connection()`  |

### Import ها

```python
# قبل
from bclib.db_context import add_db_context_services
from bclib.db_context.mongo import IMongoDbContext, add_mongodb_default_context

# بعد
from bclib.connections import add_connection_services
from bclib.connections.mongo import IMongoConnection, add_mongodb_connection
```

### استفاده در سرویس‌ها

```python
# قبل
class UserService:
    def __init__(self, db: IMongoDbContext['database.users']):
        self.db = db

# بعد
class UserService:
    def __init__(self, db: IMongoConnection['database.users']):
        self.db = db
```

## 🔧 فایل‌های به‌روزرسانی شده

### 1. `bclib/edge.py`

```python
# تغییر import
- from bclib.db_context import add_db_context_services
+ from bclib.connections import add_connection_services

# تغییر فراخوانی
- add_db_context_services(service_container)
+ add_connection_services(service_container)
```

### 2. `bclib/connections/__init__.py` (جدید)

```python
"""Database Connection Module

Provides modern database connection management inspired by ILogger<T> pattern.
"""

__all__ = ['add_connection_services']

from bclib.di import IServiceContainer

def add_connection_services(service_container: IServiceContainer) -> IServiceContainer:
    """Register Database Connection Services in DI Container"""
    from .mongo import add_mongodb_connection
    return add_mongodb_connection(service_container)
```

### 3. `bclib/connections/mongo/__init__.py` (جدید)

```python
from .imongo_connection import IMongoConnection

__all__ = ['IMongoConnection', 'add_mongodb_connection']

def add_mongodb_connection(service_container: IServiceContainer) -> IServiceContainer:
    """Register MongoDB Connection Services in DI Container"""
    # ...
```

### 4. `bclib/connections/mongo/imongo_connection.py` (جدید)

```python
class IMongoConnection(Generic[T], ABC):
    """MongoDB Connection Interface - Similar to ILogger<T> pattern."""
    # ...
```

### 5. `bclib/connections/mongo/mongo_connection.py` (جدید)

```python
class MongoConnection(IMongoConnection[T]):
    """MongoDB Connection Implementation"""
    # ...
```

## ⚠️ Breaking Changes

این یک **breaking change** است و نیاز به به‌روزرسانی کد موجود دارد:

### 1. Import ها را به‌روزرسانی کنید

```python
# قبل
from bclib.db_context.mongo import IMongoDbContext

# بعد
from bclib.connections.mongo import IMongoConnection
```

### 2. Type Annotation ها را تغییر دهید

```python
# قبل
def __init__(self, db: IMongoDbContext['database.users']):
    pass

# بعد
def __init__(self, db: IMongoConnection['database.users']):
    pass
```

### 3. نام کلاس‌ها را به‌روزرسانی کنید

```python
# قبل - اگر از وراثت استفاده می‌کردید (توصیه نمی‌شود)
class MyContext(MongoDbContext['config.key']):
    pass

# بعد
class MyConnection(MongoConnection['config.key']):
    pass
```

## ✅ مزایای این تغییر

1. **مفهوم واضح‌تر**: `Connection` نسبت به `Context` معنای واضح‌تری برای اتصال به پایگاه داده دارد

2. **معماری بهتر**: آماده برای افزودن provider های دیگر:

   - PostgreSQL Connection
   - SQL Server Connection
   - Redis Connection
   - RabbitMQ Connection

3. **سازگاری**: الگوی بهتری برای مدیریت اتصالات مختلف

4. **توسعه‌پذیری**: ساختار جدید اضافه کردن provider های جدید را آسان‌تر می‌کند

## 📦 فایل‌های حذف شده

- `bclib/db_context/` (کل پوشه و محتویات آن)
  - `__init__.py`
  - `mongo/__init__.py`
  - `mongo/imongo_db_context.py`
  - `mongo/mongo_db_context.py`
  - `mongo/MONGODB_CONTEXT_README.md`

## 📚 فایل‌های جدید

- `bclib/connections/` (پوشه جدید)
  - `__init__.py`
  - `mongo/__init__.py`
  - `mongo/imongo_connection.py`
  - `mongo/mongo_connection.py`
  - `mongo/MONGODB_CONNECTION_README.md`

## 🔍 چک‌لیست Migration

- [x] تغییر ساختار پوشه از `db_context` به `connections`
- [x] تغییر نام کلاس‌ها از `DbContext` به `Connection`
- [x] تغییر نام interface ها از `IMongoDbContext` به `IMongoConnection`
- [x] تغییر نام توابع helper
- [x] به‌روزرسانی `bclib/edge.py`
- [x] حذف فایل‌های قدیمی `db_context`
- [x] ایجاد مستندات جدید README
- [ ] به‌روزرسانی تست‌ها (در صورت نیاز)
- [ ] به‌روزرسانی مستندات پروژه اصلی
- [ ] اطلاع‌رسانی به توسعه‌دهندگان

## 🚀 نحوه استفاده بعد از Migration

```python
from bclib import edge
from bclib.connections.mongo import IMongoConnection

# تنظیم
options = {
    "database": {
        "users": {
            "connection_string": "mongodb://localhost:27017",
            "database_name": "myapp_users"
        }
    }
}

app = edge.from_options(options)

# استفاده در سرویس
class UserService:
    def __init__(self, db: IMongoConnection['database.users']):
        self.users = db.get_collection('users')

    def get_user(self, user_id: str):
        return self.users.find_one({'_id': user_id})
```

## 📞 پشتیبانی

برای سوالات یا مشکلات مربوط به migration، لطفاً:

1. مستندات جدید را در `MONGODB_CONNECTION_README.md` مطالعه کنید
2. در صورت نیاز، یک Issue در GitHub ایجاد کنید

---

**تاریخ Migration**: دسامبر 2025  
**نسخه**: 2.0.0
