# WebSocket Chat Example

یک نمونه کامل از چت گروهی با استفاده از WebSocket و قابلیت گروه‌بندی session‌ها.

## فایل‌ها

- **server.py** - سرور چت (با پشتیبانی از اتاق‌های چت)
- **client.py** - کلاینت کنسول (Python)
- **chat.html** - کلاینت مرورگر (HTML/JavaScript)

## قابلیت‌ها

✅ اتاق‌های چت (Chat Rooms) - کاربران می‌توانند به اتاق‌های مختلف بپیوندند
✅ پیام‌رسانی گروهی - پیام‌ها فقط به اعضای همان اتاق ارسال می‌شود
✅ دستورات چت - مدیریت اتاق‌ها با دستورات ساده
✅ پشتیبانی از چند کلاینت همزمان
✅ رابط کاربری زیبا برای مرورگر

## نحوه استفاده

### 1. اجرای سرور

```bash
python test/websocket/chat/server.py
```

سرور روی `ws://localhost:8080` اجرا می‌شود.

### 2. اجرای کلاینت کنسول

در یک ترمینال جدید:

```bash
python test/websocket/chat/client.py
```

یا با نام کاربری:

```bash
python test/websocket/chat/client.py Alice
```

### 3. استفاده از کلاینت مرورگر

فایل `chat.html` را در مرورگر باز کنید:

```bash
# Windows
start test/websocket/chat/chat.html

# Linux/Mac
open test/websocket/chat/chat.html
```

## دستورات چت

| دستور          | توضیحات                       |
| -------------- | ----------------------------- |
| `/join <room>` | پیوستن به اتاق چت             |
| `/leave`       | خروج از تمام اتاق‌ها          |
| `/list`        | نمایش لیست تمام اتاق‌ها       |
| `/rooms`       | نمایش اتاق‌های من             |
| `/help`        | نمایش راهنما                  |
| `/quit`        | خروج از چت (فقط کلاینت کنسول) |

## مثال استفاده

### سناریو 1: دو کاربر در یک اتاق

**کاربر 1:**

```
[Alice] /join general
[SYSTEM] Joined room: general
[Alice] Hello everyone!
```

**کاربر 2:**

```
[Bob] /join general
[SYSTEM] Joined room: general
[general] Alice: Hello everyone!
[Bob] Hi Alice!
```

### سناریو 2: اتاق‌های متعدد

**کاربر 1:**

```
[Alice] /join tech
[SYSTEM] Joined room: tech
[Alice] /join random
[SYSTEM] Joined room: random
[Alice] /rooms
[SYSTEM] Your rooms: tech, random
```

## معماری

### Server-Side (server.py)

```python
# استفاده از WebSocketSessionManager
session_manager.add_to_group(session_id, "room_name")
await session_manager.send_to_group("room_name", message, "json")
```

### Client-Side

**Python Client:**

```python
async with session.ws_connect(url) as ws:
    await ws.send_str(message)
    async for msg in ws:
        # Handle message
```

**Browser Client:**

```javascript
ws = new WebSocket("ws://localhost:8080");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle message
};
ws.send(message);
```

## ساختار پیام‌ها

### پیام سیستمی

```json
{
  "type": "system",
  "message": "Welcome to chat!"
}
```

### پیام چت

```json
{
  "type": "message",
  "room": "general",
  "sender": "abc12345",
  "message": "Hello!"
}
```

### پیام خطا

```json
{
  "type": "error",
  "message": "You are not in any room"
}
```

## تست با چند کلاینت

برای تست کامل، چند کلاینت را همزمان اجرا کنید:

```bash
# Terminal 1 - Server
python test/websocket/chat/server.py

# Terminal 2 - Client 1
python test/websocket/chat/client.py Alice

# Terminal 3 - Client 2
python test/websocket/chat/client.py Bob

# Browser - Client 3
# Open chat.html
```

سپس در هر کلاینت:

1. به یک اتاق بپیوندید: `/join general`
2. پیام بفرستید
3. پیام‌ها را در تمام کلاینت‌ها ببینید

## نکات

- هر session یک ID منحصر به فرد دارد
- session ها می‌توانند به چند اتاق همزمان بپیوندند
- پیام‌ها فقط به اعضای همان اتاق ارسال می‌شوند
- وقتی کلاینت قطع می‌شود، به صورت خودکار از تمام اتاق‌ها خارج می‌شود
- اتاق‌های خالی به صورت خودکار حذف می‌شوند

## عیب‌یابی

اگر اتصال برقرار نشد:

1. مطمئن شوید سرور در حال اجراست
2. پورت 8080 آزاد باشد
3. آدرس `localhost:8080` در دسترس باشد

برای مشاهده لاگ‌ها، خروجی سرور را بررسی کنید:

```
[CONNECT] Session abc12345 connected
[MESSAGE] Session abc12345: Hello
[DISCONNECT] Session abc12345 disconnected
```
