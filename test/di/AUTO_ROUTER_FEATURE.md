# Auto-Router Generation Feature

## 📋 Summary

Added automatic router generation from registered handlers in `RoutingDispatcher`. Router configuration in options is now **optional** - if not provided, it will be auto-generated based on handler registration.

## 🎯 Changes

### Modified Files

- `bclib/dispatcher/routing_dispatcher.py`

### New Methods

1. **`__build_router_from_lookup()`**

   - Auto-generates router from registered handlers in `__look_up`
   - Maps context types to router names:
     - `RESTfulContext` → "restful"
     - `WebContext` → "web"
     - `SocketContext` → "socket"
     - `WebSocketContext` → "websocket"
     - `ClientSourceContext` → "client_source"
     - `ServerSourceContext` → "server_source"
   - Uses first registered context type as default

2. **`__ensure_router_initialized()`**
   - Lazy initialization of router
   - Called before first message processing
   - Auto-generates if no manual config provided

### Modified Methods

- **`__init__()`**

  - Changed `__context_type_detector` to Optional (None by default)
  - Removed warning message when router not configured
  - Added comment about auto-generation

- **`_on_message_receive_async()`**
  - Added call to `__ensure_router_initialized()`
  - Ensures router is ready before processing messages

## ✨ Benefits

### 1. **Less Boilerplate**

```python
# Before (required router config)
options = {
    "server": "localhost:8080",
    "router": "restful"  # ❌ Must specify
}

# After (auto-generated)
options = {
    "server": "localhost:8080"  # ✅ That's it!
}
```

### 2. **Automatic Adaptation**

Router automatically adapts to registered handlers:

```python
@app.restful_action(app.url("api/users"))
async def get_users():
    return {"users": []}

# Router auto-generated as "restful"
```

### 3. **Backward Compatible**

All existing manual router configurations still work:

```python
# Manual config still works (takes precedence)
options = {
    "router": {
        "restful": ["api/*"],
        "web": ["*"]
    }
}
```

### 4. **Smart Defaults**

- First registered context type becomes default
- Supports multiple context types
- Falls back to "socket" if no handlers registered

## 📖 Usage Examples

### Simple Auto-Generation

```python
from bclib import edge

app = edge.from_options({"server": "localhost:8080"})

@app.restful_action(app.url("api/data"))
async def get_data():
    return {"data": "test"}

# Router auto-generated as "restful"
app.listening()
```

### Mixed Context Types

```python
app = edge.from_options({"server": "localhost:8080"})

@app.restful_action(app.url("api/users"))
async def api_handler():
    return {"users": []}

@app.websocket_action()
async def ws_handler(context):
    return {"status": "connected"}

# First registered (restful) becomes default
app.listening()
```

### Manual Override (Legacy)

```python
# Pattern-based routing (advanced scenarios)
options = {
    "router": {
        "restful": ["api/.*"],
        "websocket": ["ws/.*"],
        "web": ["*"]
    }
}

app = edge.from_options(options)
# Manual config takes precedence
```

## 🧪 Testing

### Test Files

- `test/di/test_auto_router.py` - Unit tests for auto-generation
- `test/di/example_auto_router.py` - Simple usage example
- `test/di/example_router_comparison.py` - Comparison of approaches

### Test Results

```
✅ test_auto_router.py - All 3 tests passed
✅ test_register_handler.py - All 11 tests passed (backward compatibility)
```

## 🎯 Recommendations

### When to Use Auto-Generation

- ✓ Single context type applications
- ✓ Prototyping / simple apps
- ✓ Want minimal configuration
- ✓ RESTful APIs without complex routing

### When to Use Manual Config

- ✓ Complex URL pattern routing
- ✓ Multiple context types with URL prefixes
- ✓ Need catch-all patterns
- ✓ Migrating from older versions
- ✓ Fine-grained control required

### Best Practice

1. Start with auto-generation (simplest)
2. Add manual config only when URL patterns needed
3. Both approaches can coexist
4. Manual config always takes precedence

## 🔄 Migration Path

### Existing Code (No Changes Required)

All existing configurations continue to work:

```python
# These all still work:
{"router": "restful"}
{"router": {"restful": ["api/*"]}}
{"defaultRouter": "restful"}
```

### New Code (Simplified)

New applications can omit router config entirely:

```python
# Just works!
app = edge.from_options({"server": "localhost:8080"})
```

## 📝 Implementation Details

### Lazy Initialization

Router is initialized on first message, not at construction:

- Allows all decorators to register handlers first
- Ensures complete handler lookup before analysis
- No performance impact (one-time check)

### Context Type Detection

```python
# Access parent's __look_up
lookup = self._Dispatcher__look_up

# Map context types to names
context_to_router = {
    RESTfulContext: "restful",
    # ... etc
}

# Find registered types
available = [context_to_router[t] for t in lookup.keys()]
```

### Default Selection

First registered context type becomes default:

```python
if available_routers:
    default = available_routers[0]  # First wins
    self.__context_type_detector = lambda _: default
```

## 🎉 Summary

**Router configuration is now optional!** The framework automatically detects context types from registered handlers, reducing boilerplate while maintaining full backward compatibility with manual configuration.
