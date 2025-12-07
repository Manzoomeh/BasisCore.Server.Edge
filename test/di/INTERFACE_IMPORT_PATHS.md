"""
توضیحات مربوط به استفاده از مسیرهای مختلف برای Import کردن Interface ها در DI

سوال: آیا استفاده از مسیرهای مختلف برای import کردن interface ها در registration و injection مشکل ایجاد میکنه؟

پاسخ: خیر، هیچ مشکلی ایجاد نمیشه! ✅

# دلیل:

Python از سیستم module caching استفاده میکنه. وقتی یک module اولین بار import میشه،
Python اون رو در sys.modules ذخیره میکنه. import های بعدی از همون cached object استفاده میکنن.

## مثال:

# Import از package

from bclib.options import IOptions # → bclib.options.**init** → from .ioptions import IOptions

# Import مستقیم

from bclib.options.ioptions import IOptions # → مستقیما از ioptions.py

هر دو به همان object اشاره میکنن چون:

1. Python فایل ioptions.py رو فقط یکبار load میکنه
2. Class IOptions در memory فقط یکبار ساخته میشه
3. تمام import ها به همون instance اشاره میکنن

# تست های انجام شده:

✅ Test 1: IOptions Identity

- Import از bclib.options
- Import از bclib.options.ioptions
- نتیجه: هر دو یکسان هستند (id یکسان)

✅ Test 2: ILogService Identity

- Import از bclib.log_service
- Import از bclib.log_service.ilog_service
- نتیجه: هر دو یکسان هستند

✅ Test 3: IDbManager Identity

- Import از bclib.db_manager
- Import از bclib.db_manager.idb_manager
- نتیجه: هر دو یکسان هستند

✅ Test 4: Mixed Imports in Constructor

- کلاسی که از import های مختلف استفاده میکنه
- DI میتونه به درستی dependency ها رو inject کنه
- نتیجه: کاملا کار میکنه

# کد نمونه از edge.py:

```python
# در edge.py - Registration
from bclib.options import IOptions, add_options_service
from bclib.log_service import ILogService, add_log_service
from bclib.db_manager import DbManager, IDbManager

# Register services
add_options_service(service_provider, options)
add_log_service(service_provider)
service_provider.add_singleton(IDbManager, DbManager)
```

```python
# در user code - Injection
from bclib.options.ioptions import IOptions      # مسیر مستقیم
from bclib.log_service import ILogService        # مسیر package
from bclib.db_manager.idb_manager import IDbManager  # مسیر مستقیم

class MyService:
    def __init__(self, config: IOptions['db'], logger: ILogService, db: IDbManager):
        # همه dependency ها به درستی inject میشن ✅
        self.config = config
        self.logger = logger
        self.db = db
```

# نتیجه گیری:

✅ استفاده از مسیرهای مختلف برای import کردن interface ها هیچ مشکلی ایجاد نمیکنه

✅ DI Container به درستی service ها رو resolve میکنه چون Python از object identity استفاده میکنه

✅ بهتر است از consistent import pattern استفاده کنید برای خوانایی کد:

- توصیه: همیشه از package-level import استفاده کنید
- مثال: from bclib.options import IOptions
- به جای: from bclib.options.ioptions import IOptions

✅ اما اگر کاربر از مسیر متفاوت import کنه، باز هم مشکلی نیست و DI درست کار میکنه

# تست اضافی - Generic Types:

حتی با Generic type ها هم مشکلی نیست:

```python
# Registration در edge.py
from bclib.options import IOptions
add_options_service(service_provider, options)

# Injection در user code
from bclib.options.ioptions import IOptions  # مسیر متفاوت

class Service:
    def __init__(self, config: IOptions['database']):  # ✅ کار میکنه
        self.config = config
```

چون IOptions[ForwardRef('database')] هم به همان base class IOptions اشاره میکنه.

# Technical Details:

وقتی Python یک module رو import میکنه:

1. Check میکنه آیا module در sys.modules هست یا نه
2. اگر هست، همون cached object رو برمیگردونه
3. اگر نیست، module رو load کنه و در sys.modules ذخیره میکنه

مثال:

```python
import sys
from bclib.options import IOptions as IOptions1
from bclib.options.ioptions import IOptions as IOptions2

print(IOptions1 is IOptions2)  # True
print(id(IOptions1) == id(IOptions2))  # True

# همچنین در sys.modules
print(sys.modules['bclib.options.ioptions'])  # همون module
```

DI Container از isinstance و type identity برای matching استفاده میکنه:

```python
# در service_provider.py
if service_type in self._descriptors:  # type identity check
    descriptor = self._descriptors[service_type]
```

چون service_type همیشه به همان object اشاره میکنه، matching درست کار میکنه.

# خلاصه:

استفاده از مسیرهای مختلف برای import:

- ✅ مشکلی ایجاد نمیکنه
- ✅ DI Container به درستی کار میکنه
- ✅ Object identity حفظ میشه
- ✅ Generic type ها هم درست کار میکنن
- ⚠️ اما بهتر است از یک pattern استفاده کنید برای consistency

توصیه: همیشه از package-level imports استفاده کنید:

```python
from bclib.options import IOptions
from bclib.log_service import ILogService
from bclib.db_manager import IDbManager
```

"""
