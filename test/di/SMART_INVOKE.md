# Smart Invoke - تشخیص خودکار Sync/Async

## خلاصه

متد `invoke()` در `ServiceProvider` به طور هوشمند تشخیص می‌دهد که تابع sync است یا async و به طور خودکار متد مناسب را فراخوانی می‌کند.

## چرا Smart Invoke؟

قبل از Smart Invoke، باید می‌دانستید تابع async است یا sync:

```python
# ❌ روش قدیمی - باید بدانید تابع چه نوعی است
result = services.invoke_method(sync_function, data="test")
result = await services.invoke_method_async(async_function, data="test")
```

با Smart Invoke:

```python
# ✅ روش جدید - خودش تشخیص می‌دهد!
result = await services.invoke(any_function, data="test")
```

## نحوه استفاده

### با توابع Sync

```python
def calculate(logger: ILogger, a: int, b: int) -> int:
    logger.log(f"Calculating {a} + {b}")
    return a + b

# Smart invoke تشخیص می‌دهد sync است
result = services.invoke(calculate, a=10, b=5)  # بدون await
```

### با توابع Async

```python
async def save_data(logger: ILogger, db: IDatabase, data: dict) -> bool:
    logger.log("Saving data...")
    return await db.save(data)

# Smart invoke تشخیص می‌دهد async است
result = await services.invoke(save_data, data={...})  # با await
```

### در Handlers

```python
@app.restful_handler()
async def handler(context: RESTfulContext):
    # یک خط برای هر دو نوع تابع!
    result = await context.services.invoke(some_function, param="value")
    return {"result": result}
```

## چگونه کار می‌کند؟

```python
def invoke(self, method: Callable, *args, **kwargs):
    # استفاده از inspect.iscoroutinefunction()
    if inspect.iscoroutinefunction(method):
        return self.invoke_method_async(method, *args, **kwargs)
    else:
        return self.invoke_method(method, *args, **kwargs)
```

## مزایا

✅ **یک API واحد**: دیگر نیازی به انتخاب بین دو متد نیست  
✅ **کد تمیزتر**: همه جا از `invoke()` استفاده کنید  
✅ **کمتر خطا**: خطای "forgot await" کمتر می‌شود  
✅ **انعطاف‌پذیر**: تابع را می‌توانید از sync به async تغییر دهید بدون تغییر caller

## مقایسه

| ویژگی           | invoke_method   | invoke_method_async | invoke ⭐      |
| --------------- | --------------- | ------------------- | -------------- |
| Sync Functions  | ✅              | ❌                  | ✅             |
| Async Functions | ❌              | ✅                  | ✅             |
| تشخیص خودکار    | ❌              | ❌                  | ✅             |
| نیاز به await   | ❌              | ✅                  | وابسته به تابع |
| توصیه           | برای sync مطمئن | برای async مطمئن    | **همیشه**      |

## مثال کامل

```python
from bclib.utility import ServiceProvider
from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass

class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"[LOG] {message}")

# توابع business logic
def validate_email(logger: ILogger, email: str) -> bool:
    logger.log(f"Validating: {email}")
    return "@" in email

async def send_email(logger: ILogger, to: str, message: str) -> bool:
    logger.log(f"Sending to: {to}")
    # await some async operation
    return True

# Setup DI
services = ServiceProvider()
services.add_singleton(ILogger, ConsoleLogger)

# استفاده - یک روش برای هر دو!
async def main():
    # Sync function
    is_valid = services.invoke(validate_email, email="test@example.com")
    print(f"Valid: {is_valid}")

    # Async function
    sent = await services.invoke(send_email, to="user@example.com", message="Hello")
    print(f"Sent: {sent}")

import asyncio
asyncio.run(main())
```

## نکات مهم

1. **همیشه await کنید**: در async context، همیشه با `await` استفاده کنید:

   ```python
   result = await services.invoke(function, ...)
   ```

2. **برای sync هم کار می‌کند**: اگر تابع sync باشد، مستقیماً نتیجه را برمی‌گرداند

3. **Type hints مهم است**: پارامترهای type-hinted به طور خودکار inject می‌شوند

4. **پارامترهای صریح اولویت دارند**: اگر پارامتری را صریح بدهید، از DI استفاده نمی‌شود

## تست

برای تست این قابلیت:

```bash
python test/di/test_smart_invoke.py
```

یا سرور کامل:

```bash
python test/di/method_injection.py
# سپس: http://localhost:8094/smart-invoke/demo
```
