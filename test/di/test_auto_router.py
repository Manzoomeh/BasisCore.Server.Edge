"""Test auto-generation of router from handler lookup"""
from bclib import edge
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


# Test 1: Auto-generate router from RESTful handlers
print("Test 1: Auto-generate router with RESTful handlers")
options = {
    "server": "localhost:8080",
    "log_request": False
}

app = edge.from_options(options)


@app.restful_action(app.url("api/users"))
async def get_users():
    return {"users": ["Alice", "Bob"]}


@app.restful_action(app.url("api/posts"))
async def get_posts():
    return {"posts": ["Post 1", "Post 2"]}

# Access private attribute to check router
detector = app._RoutingDispatcher__context_type_detector
if detector is None:
    print("✅ Router not initialized yet (lazy initialization)")
else:
    print(f"❌ Router should be None before first message")

# Simulate initialization
app._RoutingDispatcher__ensure_router_initialized()

# Check if router was auto-generated
default_router = app._RoutingDispatcher__default_router
print(f"Default router: {default_router}")
if default_router == "restful":
    print("✅ Router auto-generated as 'restful'")
else:
    print(f"❌ Expected 'restful', got '{default_router}'")

print()

# Test 2: Auto-generate with multiple context types
print("Test 2: Auto-generate router with multiple context types")
options2 = {
    "server": "localhost:8081",
    "log_request": False
}

app2 = edge.from_options(options2)


@app2.restful_action(app2.url("api/data"))
async def get_data():
    return {"data": "test"}


@app2.websocket_action()
async def handle_ws(context):
    return {"message": "connected"}


@app2.web_action(app2.url("index.html"))
async def get_index():
    return "<html>Hello</html>"

# Initialize router
app2._RoutingDispatcher__ensure_router_initialized()
default_router2 = app2._RoutingDispatcher__default_router

print(f"Default router: {default_router2}")
if default_router2 in ["restful", "websocket", "web"]:
    print(f"✅ Router auto-generated as '{default_router2}' (first registered)")
else:
    print(f"❌ Expected one of the registered types, got '{default_router2}'")

print()

# Test 3: Manual router config still works
print("Test 3: Manual router configuration (backward compatibility)")
options3 = {
    "server": "localhost:8082",
    "router": "web",
    "log_request": False
}

app3 = edge.from_options(options3)


@app3.web_action(app3.url("*"))
async def catch_all():
    return "Catch all"

default_router3 = app3._RoutingDispatcher__default_router
detector3 = app3._RoutingDispatcher__context_type_detector

if detector3 is not None and default_router3 is None:
    result = detector3("any_url")
    if result == "web":
        print("✅ Manual router config still works")
    else:
        print(f"❌ Expected 'web', got '{result}'")
else:
    print(f"❌ Router not properly initialized with manual config")

print()
print("All tests completed!")
