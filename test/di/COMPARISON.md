# Service Registration Comparison

## قبل (با ارث‌بری)

```python
from bclib import edge
from bclib.utility import ServiceProvider

# باید یک کلاس جدید بسازید
class MyDispatcher(edge.DevServerDispatcher):
    def _configure_services(self, services: ServiceProvider):
        # ثبت سرویس‌ها
        services.add_singleton(ILogger, ConsoleLogger)
        services.add_scoped(IDatabase, PostgresDatabase)
        services.add_transient(IEmailService, SmtpEmailService)

# ایجاد instance از کلاس جدید
options = {"server": "localhost:8080", "router": "restful"}
app = MyDispatcher(options)

# ثبت handlerها
@app.restful_handler()
async def handler(context):
    return {"status": "ok"}

app.listening()
```

**خطوط کد:** ~15 خط  
**نیاز:** کلاس جدید + override method

---

## بعد (بدون ارث‌بری) ⭐

```python
from bclib import edge

# مستقیماً از DevServerDispatcher استفاده کنید
options = {"server": "localhost:8080", "router": "restful"}
app = edge.DevServerDispatcher(options)

# ثبت سرویس‌ها با callback
app.configure_services(lambda services: (
    services.add_singleton(ILogger, ConsoleLogger),
    services.add_scoped(IDatabase, PostgresDatabase),
    services.add_transient(IEmailService, SmtpEmailService)
))

# ثبت handlerها
@app.restful_handler()
async def handler(context):
    return {"status": "ok"}

app.listening()
```

**خطوط کد:** ~10 خط  
**نیاز:** هیچ چیز اضافه!

---

## مزایای روش جدید

### ✅ کد کمتر

- بدون کلاس جدید
- بدون override method
- کد تمیزتر و خواناتر

### ✅ یادگیری آسان‌تر

- نیازی به درک inheritance نیست
- مفاهیم ساده‌تر
- مناسب مبتدی‌ها

### ✅ سریع‌تر برای prototype

- کد کمتر = توسعه سریع‌تر
- مناسب برای تست و آزمایش
- کمتر boilerplate

### ✅ انعطاف‌پذیر

- می‌توان چندین بار فراخوانی کرد
- پشتیبانی از method chaining
- ترکیب configuration های مختلف

---

## کدام روش را انتخاب کنیم؟

### استفاده از `configure_services()` (بدون ارث‌بری) وقتی که:

- ⭐ برنامه کوچک یا متوسط است
- در حال یادگیری DI هستید
- می‌خواهید سریع prototype بسازید
- فقط نیاز به ثبت سرویس دارید
- ترجیح می‌دهید کد ساده‌تری داشته باشید

### استفاده از `_configure_services()` (با ارث‌بری) وقتی که:

- برنامه بزرگ و پیچیده است
- نیاز به override کردن متدهای دیگر dispatcher دارید
- می‌خواهید logic پیچیده‌ای در initialization داشته باشید
- تیم شما الگوی OOP را ترجیح می‌دهد
- نیاز به چندین dispatcher با تنظیمات مختلف دارید

---

## مثال ترکیبی

می‌توانید هر دو روش را با هم استفاده کنید:

```python
class MyDispatcher(edge.DevServerDispatcher):
    def _configure_services(self, services: ServiceProvider):
        # سرویس‌های پایه
        services.add_singleton(ILogger, ConsoleLogger)

# ایجاد instance
app = MyDispatcher(options)

# اضافه کردن سرویس‌های بیشتر
app.configure_services(lambda services:
    services.add_scoped(IDatabase, PostgresDatabase)
)
```

---

## خلاصه

| معیار      | با ارث‌بری      | بدون ارث‌بری ⭐ |
| ---------- | --------------- | --------------- |
| خطوط کد    | 15+             | 10              |
| سادگی      | متوسط           | ساده            |
| سرعت توسعه | معمولی          | سریع            |
| مناسب برای | برنامه‌های بزرگ | برنامه‌های کوچک |
| یادگیری    | نیاز به OOP     | ساده            |
| انعطاف     | کامل            | خوب             |

**توصیه:** برای شروع از روش بدون ارث‌بری استفاده کنید و در صورت نیاز به امکانات پیشرفته، به روش ارث‌بری مهاجرت کنید.
