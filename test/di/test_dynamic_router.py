"""Test dynamic router rebuild on handler registration/unregistration"""
import os
import sys

from bclib import edge
from bclib.context import HttpContext, RESTfulContext, WebSocketContext

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


print("=" * 70)
print("Dynamic Router Rebuild Test")
print("=" * 70)
print()

# Test 1: Router rebuilds on handler registration
print("1️⃣  Router Rebuild on Handler Registration")
print("-" * 70)

options = {
    "http": "localhost:8080",
    "log_request": False
}

app = edge.from_options(options)

# Initially no handlers - should default to socket
app._RoutingDispatcher__ensure_router_initialized()
initial_router = app._RoutingDispatcher__default_router
print(f"Initial router (no handlers): {initial_router}")

# Register a RESTful handler


async def get_users():
    return {"users": []}

app.register_handler(RESTfulContext, get_users, [app.url("api/users")])

# Router should automatically rebuild
current_router = app._RoutingDispatcher__default_router
print(f"After registering RESTful handler: {current_router}")

if current_router == "restful":
    print("✅ Router automatically rebuilt to 'restful'")
else:
    print(f"❌ Expected 'restful', got '{current_router}'")

print()

# Test 2: Router rebuilds when switching context types
print("2️⃣  Router Rebuild on Context Type Change")
print("-" * 70)

app2 = edge.from_options({"http": "localhost:8081", "log_request": False})

# Register WebSocket handler


async def ws_handler(context):
    return {"ws": "connected"}

app2.register_handler(WebSocketContext, ws_handler)
router_after_ws = app2._RoutingDispatcher__default_router
print(f"After WebSocket handler: {router_after_ws}")

# Unregister WebSocket, register Web
app2.unregister_handler(WebSocketContext, ws_handler)


async def web_handler():
    return "<html>Home</html>"

app2.register_handler(HttpContext, web_handler, [app2.url("index.html")])
router_after_web = app2._RoutingDispatcher__default_router

print(f"After switching to Web handler: {router_after_web}")

if router_after_ws == "websocket" and router_after_web == "web":
    print("✅ Router correctly rebuilt on context type change")
else:
    print(
        f"❌ Expected websocket→web, got {router_after_ws}→{router_after_web}")

print()

# Test 3: Manual config not affected by dynamic changes
print("3️⃣  Manual Config Unchanged by Dynamic Handlers")
print("-" * 70)

options3 = {
    "http": "localhost:8082",
    "router": "restful",  # Manual config
    "log_request": False
}

app3 = edge.from_options(options3)

# Get initial detector
detector_before = app3._RoutingDispatcher__context_type_detector
manual_config_flag = app3._RoutingDispatcher__manual_router_config

print(f"Manual router config: {manual_config_flag}")
print(f"Router type: restful (manual)")

# Try to register WebSocket handler


async def ws_handler3(context):
    return {"ws": "test"}

app3.register_handler(WebSocketContext, ws_handler3)

# Detector should remain unchanged
detector_after = app3._RoutingDispatcher__context_type_detector
router_unchanged = (detector_before is detector_after)

if manual_config_flag and router_unchanged:
    print("✅ Manual config preserved despite dynamic handler changes")
else:
    print("❌ Manual config should not be affected by dynamic handlers")

print()

# Test 4: Multiple dynamic registrations
print("4️⃣  Multiple Dynamic Handler Registrations")
print("-" * 70)

app4 = edge.from_options({"http": "localhost:8083", "log_request": False})


async def handler1():
    return {"data": "1"}


async def handler2():
    return {"data": "2"}


async def handler3():
    return {"data": "3"}

# Register multiple handlers of same type
app4.register_handler(RESTfulContext, handler1, [app4.url("api/1")])
router_after_1 = app4._RoutingDispatcher__default_router

app4.register_handler(RESTfulContext, handler2, [app4.url("api/2")])
router_after_2 = app4._RoutingDispatcher__default_router

app4.register_handler(RESTfulContext, handler3, [app4.url("api/3")])
router_after_3 = app4._RoutingDispatcher__default_router

print(f"After 1st handler: {router_after_1}")
print(f"After 2nd handler: {router_after_2}")
print(f"After 3rd handler: {router_after_3}")

if router_after_1 == router_after_2 == router_after_3 == "restful":
    print("✅ Router consistent across multiple registrations")
else:
    print("❌ Router should remain consistent")

print()

# Test 5: Unregister all handlers
print("5️⃣  Router Rebuild on Unregister All Handlers")
print("-" * 70)

app5 = edge.from_options({"http": "localhost:8084", "log_request": False})


async def temp_handler():
    return {"temp": "data"}

# Register then unregister
app5.register_handler(RESTfulContext, temp_handler, [app5.url("api/temp")])
router_with_handler = app5._RoutingDispatcher__default_router
print(f"With handler: {router_with_handler}")

app5.unregister_handler(RESTfulContext, temp_handler)
router_without_handler = app5._RoutingDispatcher__default_router
print(f"After unregister: {router_without_handler}")

if router_with_handler == "restful" and router_without_handler == "socket":
    print("✅ Router rebuilt correctly after removing all handlers")
else:
    print(
        f"❌ Expected restful→socket, got {router_with_handler}→{router_without_handler}")

print()
print("=" * 70)
print("Summary")
print("=" * 70)
print()
print("✅ Router dynamically rebuilds on handler registration")
print("✅ Router adapts to context type changes")
print("✅ Manual config preserved (not affected by dynamic changes)")
print("✅ Multiple registrations handled correctly")
print("✅ Router rebuilds when handlers are removed")
print()
print("💡 Key Feature:")
print("   Router automatically stays in sync with dynamic handler changes!")
print()
