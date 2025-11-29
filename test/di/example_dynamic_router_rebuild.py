"""Example: Dynamic Handler Management with Auto Router Rebuild"""
from bclib.context import RESTfulContext, WebSocketContext
from bclib import edge
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


print("=" * 70)
print("Dynamic Handler Management Example")
print("=" * 70)
print()

# Scenario: Hot-swapping API versions
print("📦 Scenario: Hot-Swapping API Versions")
print("-" * 70)

app = edge.from_options({"http": "localhost:8080"})

# Version 1 handlers


async def get_users_v1():
    return {
        "version": "1.0",
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }


async def get_posts_v1():
    return {
        "version": "1.0",
        "posts": ["Post 1", "Post 2"]
    }

# Version 2 handlers (improved with pagination)


async def get_users_v2():
    return {
        "version": "2.0",
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "pagination": {"page": 1, "total": 2}
    }


async def get_posts_v2():
    return {
        "version": "2.0",
        "posts": [
            {"id": 1, "title": "Post 1", "author": "Alice"},
            {"id": 2, "title": "Post 2", "author": "Bob"}
        ],
        "pagination": {"page": 1, "total": 2}
    }

print("1. Deploying Version 1.0...")
app.register_handler(RESTfulContext, get_users_v1, [app.url("api/users")])
app.register_handler(RESTfulContext, get_posts_v1, [app.url("api/posts")])
router_v1 = app._RoutingDispatcher__default_router
print(f"   ✓ Active handlers: get_users_v1, get_posts_v1")
print(f"   ✓ Router: {router_v1}")
print()

print("2. Hot-swap to Version 2.0...")
# Remove v1 handlers
app.unregister_handler(RESTfulContext, get_users_v1)
app.unregister_handler(RESTfulContext, get_posts_v1)

# Add v2 handlers
app.register_handler(RESTfulContext, get_users_v2, [app.url("api/users")])
app.register_handler(RESTfulContext, get_posts_v2, [app.url("api/posts")])
router_v2 = app._RoutingDispatcher__default_router
print(f"   ✓ Active handlers: get_users_v2, get_posts_v2")
print(f"   ✓ Router: {router_v2}")
print(f"   ✓ Router remained consistent: {router_v1 == router_v2}")
print()

# Scenario: Adding WebSocket support dynamically
print("📦 Scenario: Adding WebSocket Support Dynamically")
print("-" * 70)

app2 = edge.from_options({"http": "localhost:8081"})

# Start with only REST API


async def rest_handler():
    return {"type": "REST"}

app2.register_handler(RESTfulContext, rest_handler, [app2.url("api/data")])
router_rest_only = app2._RoutingDispatcher__default_router
print(f"1. Initial setup (REST only)")
print(f"   ✓ Router: {router_rest_only}")
print()

# Add WebSocket support


async def ws_handler(context):
    return {"type": "WebSocket", "message": "Connected"}

print(f"2. Adding WebSocket support...")
app2.register_handler(WebSocketContext, ws_handler)
router_with_ws = app2._RoutingDispatcher__default_router
print(f"   ✓ Router: {router_with_ws}")
print(f"   ✓ Note: Router uses first registered type (REST)")
print()

# Scenario: Maintenance mode
print("📦 Scenario: Maintenance Mode Toggle")
print("-" * 70)

app3 = edge.from_options({"http": "localhost:8082"})

# Normal operation handlers


async def normal_handler():
    return {"status": "operational", "data": "Hello World"}

# Maintenance handler


async def maintenance_handler():
    return {"status": "maintenance", "message": "Service under maintenance"}

print("1. Normal operation mode")
app3.register_handler(RESTfulContext, normal_handler, [app3.url("api/*")])
print(f"   ✓ Handler: normal_handler")
print(f"   ✓ Router: {app3._RoutingDispatcher__default_router}")
print()

print("2. Switching to maintenance mode...")
app3.unregister_handler(RESTfulContext, normal_handler)
app3.register_handler(RESTfulContext, maintenance_handler, [app3.url("api/*")])
print(f"   ✓ Handler: maintenance_handler")
print(f"   ✓ Router: {app3._RoutingDispatcher__default_router}")
print(f"   ✓ Router rebuilt automatically")
print()

print("3. Back to normal operation...")
app3.unregister_handler(RESTfulContext, maintenance_handler)
app3.register_handler(RESTfulContext, normal_handler, [app3.url("api/*")])
print(f"   ✓ Handler: normal_handler")
print(f"   ✓ Router: {app3._RoutingDispatcher__default_router}")
print()

# Scenario: Feature flags
print("📦 Scenario: Feature Flags")
print("-" * 70)

app4 = edge.from_options({"http": "localhost:8083"})

# Old feature


async def feature_v1():
    return {"feature": "old", "data": "legacy data"}

# New feature


async def feature_v2():
    return {"feature": "new", "data": "improved data", "extra": "bonus"}

feature_flag_enabled = False

print(f"1. Feature flag: {feature_flag_enabled}")
if feature_flag_enabled:
    app4.register_handler(RESTfulContext, feature_v2,
                          [app4.url("api/feature")])
    print(f"   ✓ Using: feature_v2 (new)")
else:
    app4.register_handler(RESTfulContext, feature_v1,
                          [app4.url("api/feature")])
    print(f"   ✓ Using: feature_v1 (old)")
print(f"   ✓ Router: {app4._RoutingDispatcher__default_router}")
print()

# Enable feature flag
feature_flag_enabled = True
print(f"2. Feature flag: {feature_flag_enabled}")
app4.unregister_handler(RESTfulContext, feature_v1)
app4.register_handler(RESTfulContext, feature_v2, [app4.url("api/feature")])
print(f"   ✓ Switched to: feature_v2 (new)")
print(f"   ✓ Router: {app4._RoutingDispatcher__default_router}")
print(f"   ✓ Router automatically synchronized")
print()

print("=" * 70)
print("Summary")
print("=" * 70)
print()
print("Key Benefits:")
print("  ✅ Hot-swap handlers without restart")
print("  ✅ Router automatically rebuilds on changes")
print("  ✅ Perfect for A/B testing and feature flags")
print("  ✅ Maintenance mode toggle without downtime")
print("  ✅ Version management made easy")
print()
print("Use Cases:")
print("  🔄 API versioning")
print("  🚧 Maintenance mode")
print("  🎯 Feature flags / A/B testing")
print("  🔌 Plugin systems")
print("  🌐 Multi-tenant routing")
print()
