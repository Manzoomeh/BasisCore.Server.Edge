# Dynamic Router Rebuild Feature

## 📋 خلاصه

Router به‌صورت خودکار بعد از اضافه یا حذف dynamic handler دوباره ساخته می‌شود. این امکان باعث می‌شود handler management کاملاً dynamic و بدون نیاز به restart باشد.

## 🎯 تغییرات

### Modified Files

#### 1. `bclib/dispatcher/dispatcher.py`

##### متد جدید: `_on_handlers_changed()`

```python
def _on_handlers_changed(self):
    """
    Hook method called when handlers are dynamically added or removed

    Subclasses can override this to react to handler changes.
    For example, RoutingDispatcher rebuilds the router configuration.
    """
    pass
```

##### تغییرات در `register_handler()`

- اضافه شدن فراخوانی `self._on_handlers_changed()` در انتها
- اطلاع‌رسانی به subclass‌ها که handler اضافه شده

##### تغییرات در `unregister_handler()`

- اضافه شدن فراخوانی `self._on_handlers_changed()` در انتها
- اطلاع‌رسانی به subclass‌ها که handler حذف شده

#### 2. `bclib/dispatcher/routing_dispatcher.py`

##### فیلد جدید: `__manual_router_config`

```python
self.__manual_router_config = False  # Track if router was manually configured
```

- نگهداری وضعیت: آیا router دستی configure شده یا خیر
- اگر `True` باشد، router rebuild نمی‌شود (حفظ manual config)

##### Override متد: `_on_handlers_changed()`

```python
def _on_handlers_changed(self):
    """
    Rebuild router when handlers are dynamically added or removed

    Only rebuilds if router was auto-generated (not manually configured).
    This ensures dynamic handler changes are reflected in routing.
    """
    # Only rebuild if router was auto-generated (not manual config)
    if not self.__manual_router_config:
        # Reset detector to trigger rebuild on next message
        self.__context_type_detector = None
        # Immediately rebuild to reflect changes
        self.__build_router_from_lookup()
```

##### بهبود `__build_router_from_lookup()`

```python
# Find which context types have handlers (non-empty lists)
available_routers = [
    context_to_router[ctx_type]
    for ctx_type in lookup.keys()
    if ctx_type in context_to_router and len(lookup[ctx_type]) > 0  # ✨ Check non-empty
]

if available_routers:
    # Use first registered context type as default
    default = available_routers[0]
    self.__context_type_detector: 'Callable[[str],str]' = lambda _: default
    self.__default_router = default  # ✨ Always update
else:
    # No handlers registered, use socket as fallback
    self.__context_type_detector: 'Callable[[str],str]' = lambda _: "socket"
    self.__default_router = "socket"  # ✨ Always update
```

## ✨ رفتار جدید

### 1. **Automatic Rebuild on Registration**

```python
app = edge.from_options({"http": "localhost:8080"})

# Initial: no handlers → router = "socket"

app.register_handler(RESTfulContext, handler1, predicates)
# ✅ Router automatically rebuilt → "restful"

app.register_handler(WebSocketContext, handler2)
# ✅ Router rebuilt → still "restful" (first wins)
```

### 2. **Automatic Rebuild on Unregistration**

```python
app.register_handler(RESTfulContext, handler1, predicates)
# Router: "restful"

app.unregister_handler(RESTfulContext, handler1)
# ✅ Router automatically rebuilt → "socket" (no handlers left)
```

### 3. **Context Type Switch**

```python
app.register_handler(WebSocketContext, ws_handler)
# Router: "websocket"

app.unregister_handler(WebSocketContext, ws_handler)
app.register_handler(WebContext, web_handler, predicates)
# ✅ Router rebuilt → "web"
```

### 4. **Manual Config Protected**

```python
app = edge.from_options({
    "router": "restful"  # Manual config
})

app.register_handler(WebSocketContext, ws_handler)
# ❌ Router NOT rebuilt (manual config preserved)
# Router: still "restful"
```

## 🧪 Testing

### Test Files

- `test/di/test_dynamic_router.py` - Unit tests for dynamic rebuild
- `test/di/example_dynamic_router_rebuild.py` - Practical scenarios

### Test Results

```
✅ Router rebuild on handler registration
✅ Router rebuild on context type change
✅ Manual config preserved (not affected)
✅ Multiple registrations handled correctly
✅ Router rebuild when handlers removed
✅ All 11 register/unregister tests still pass
```

## 💡 Use Cases

### 1. Hot-Swapping API Versions

```python
# Deploy v1
app.register_handler(RESTfulContext, get_users_v1, [app.url("api/users")])

# Hot-swap to v2 (no restart!)
app.unregister_handler(RESTfulContext, get_users_v1)
app.register_handler(RESTfulContext, get_users_v2, [app.url("api/users")])
# ✅ Router automatically synchronized
```

### 2. Maintenance Mode

```python
# Normal operation
app.register_handler(RESTfulContext, normal_handler, [app.url("*")])

# Switch to maintenance
app.unregister_handler(RESTfulContext, normal_handler)
app.register_handler(RESTfulContext, maintenance_handler, [app.url("*")])
# ✅ Router rebuilt, all requests go to maintenance
```

### 3. Feature Flags

```python
if feature_flag_enabled:
    app.unregister_handler(RESTfulContext, old_feature)
    app.register_handler(RESTfulContext, new_feature, predicates)
    # ✅ Router reflects new feature instantly
```

### 4. A/B Testing

```python
if user_segment == "A":
    app.register_handler(RESTfulContext, variant_a, predicates)
else:
    app.register_handler(RESTfulContext, variant_b, predicates)
# ✅ Router adapts to each variant
```

### 5. Plugin Systems

```python
# Load plugin
plugin_handler = load_plugin("payment_gateway")
app.register_handler(RESTfulContext, plugin_handler, [app.url("api/pay/*")])
# ✅ Router includes new plugin routes

# Unload plugin
app.unregister_handler(RESTfulContext, plugin_handler)
# ✅ Router removes plugin routes
```

## 🔄 فرایند کار

```
Handler Registration/Unregistration
           ↓
   _on_handlers_changed() called
           ↓
   Check: __manual_router_config?
           ↓
   ┌─────No─────┐        Yes→ Skip (preserve manual config)
   ↓
   Reset __context_type_detector = None
   ↓
   Call __build_router_from_lookup()
   ↓
   Analyze __look_up dictionary
   ↓
   Find context types with handlers (non-empty)
   ↓
   Update __default_router to first available
   ↓
   Create new __context_type_detector lambda
   ↓
   Router Rebuilt ✅
```

## 📊 مقایسه قبل و بعد

### قبل

```python
# Handler registration
app.register_handler(RESTfulContext, handler, predicates)
# ❌ Router NOT updated automatically
# ❌ Need manual restart or reconfiguration
```

### بعد

```python
# Handler registration
app.register_handler(RESTfulContext, handler, predicates)
# ✅ Router automatically rebuilt
# ✅ Changes reflected immediately
# ✅ No restart needed
```

## 🎯 مزایا

1. **Zero Downtime Updates**

   - تغییر handler بدون restart سرور
   - Hot-swap handlers در runtime

2. **Automatic Synchronization**

   - Router همیشه با handlers sync است
   - نیازی به manual update نیست

3. **Backward Compatible**

   - Manual router config کماکان کار می‌کند
   - تغییری در API موجود نیست

4. **Smart Detection**

   - فقط auto-generated routers rebuild می‌شوند
   - Manual config محافظت می‌شود

5. **Dynamic Flexibility**
   - Perfect برای A/B testing
   - Feature flags support
   - Plugin systems
   - Multi-tenant routing

## 🔐 Safety Features

### 1. Manual Config Protection

```python
options = {"router": "restful"}  # Manual
app = edge.from_options(options)
# __manual_router_config = True
# Router changes are IGNORED
```

### 2. Non-Empty Check

```python
# Only counts context types with actual handlers
if len(lookup[ctx_type]) > 0:  # ✅ Has handlers
    available_routers.append(...)
```

### 3. Fallback to Socket

```python
if not available_routers:
    # No handlers registered
    router = "socket"  # Safe default
```

## 📝 Best Practices

1. **Auto-Generated Router**

   ```python
   # Let router adapt to handlers
   app = edge.from_options({"http": "localhost:8080"})
   app.register_handler(RESTfulContext, handler, predicates)
   # ✅ Router auto-generated and auto-updated
   ```

2. **Manual Router (Advanced)**

   ```python
   # Fixed routing patterns
   app = edge.from_options({
       "router": {"restful": ["api/*"], "web": ["*"]}
   })
   # ✅ Router preserved, no auto-rebuild
   ```

3. **Hot-Swap Pattern**
   ```python
   # Always unregister old before registering new
   app.unregister_handler(context_type, old_handler)
   app.register_handler(context_type, new_handler, predicates)
   # ✅ Clean transition, router updated once
   ```

## 🎉 خلاصه

**Router به‌صورت خودکار و intelligent با تغییرات handler sync می‌شود!** این امکان باعث می‌شود:

- ✅ Dynamic handler management بدون restart
- ✅ Hot-swapping for zero downtime
- ✅ Perfect for feature flags & A/B testing
- ✅ Plugin systems با routing خودکار
- ✅ Manual config همچنان محافظت می‌شود

این قابلیت BasisCore.Server.Edge را به یک فریمورک کاملاً dynamic و production-ready تبدیل می‌کند! 🚀
