"""Advanced Example: Mixed auto-router and manual patterns"""
from bclib import edge
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


print("=" * 70)
print("Auto-Router vs Manual Router Comparison")
print("=" * 70)
print()

# Example 1: Pure Auto-Generation (Simplest)
print("1️⃣  Pure Auto-Generation (Recommended for simple apps)")
print("-" * 70)
options1 = {
    "server": "localhost:8080"
}
app1 = edge.from_options(options1)


@app1.restful_handler(app1.url("api/data"))
async def get_data():
    return {"data": "test"}

app1._RoutingDispatcher__ensure_router_initialized()
print(f"   Config: No router specified")
print(
    f"   Result: Router auto-generated as '{app1._RoutingDispatcher__default_router}'")
print(f"   ✅ Minimal configuration, automatic detection")
print()

# Example 2: Simple Manual Override
print("2️⃣  Simple Manual Override")
print("-" * 70)
options2 = {
    "server": "localhost:8081",
    "router": "restful"  # Force all to RESTful
}
app2 = edge.from_options(options2)


@app2.restful_handler(app2.url("api/endpoint"))
async def handler():
    return {"status": "ok"}

print(f"   Config: router='restful'")
print(f"   Result: All requests treated as RESTful")
print(f"   ✅ Simple, explicit control")
print()

# Example 3: Pattern-Based Manual Config
print("3️⃣  Pattern-Based Manual Config (Advanced)")
print("-" * 70)
options3 = {
    "server": "localhost:8082",
    "router": {
        "restful": ["api/.*", "v1/.*"],
        "web": ["static/.*", "assets/.*"],
        "websocket": ["ws/.*"],
        "socket": ["*"]  # Catch-all
    }
}
app3 = edge.from_options(options3)


@app3.restful_handler(app3.url("api/users"))
async def api_handler():
    return {"users": []}


@app3.web_handler(app3.url("static/index.html"))
async def web_handler():
    return "<html>Home</html>"

print(f"   Config: Pattern-based routing")
print(f"   Routes:")
print(f"     - api/* → restful")
print(f"     - static/* → web")
print(f"     - ws/* → websocket")
print(f"     - * → socket (catch-all)")
print(f"   ✅ Fine-grained URL pattern control")
print()

# Example 4: Default Router with Auto-Generation
print("4️⃣  Default Router + Auto-Generation")
print("-" * 70)
options4 = {
    "server": "localhost:8083",
    "defaultRouter": "restful"
}
app4 = edge.from_options(options4)


@app4.restful_handler(app4.url("api/test"))
async def test_handler():
    return {"test": "ok"}


@app4.websocket_handler()
async def ws_handler(context):
    return {"ws": "connected"}

app4._RoutingDispatcher__ensure_router_initialized()
print(f"   Config: defaultRouter='restful'")
print(f"   Result: Falls back to 'restful' when auto-detection fails")
print(f"   Handlers: RESTful + WebSocket registered")
print(f"   ✅ Safety net for mixed context types")
print()

# Summary
print("=" * 70)
print("📋 Summary & Recommendations")
print("=" * 70)
print()
print("Use Auto-Generation when:")
print("  ✓ Single context type (all RESTful, all WebSocket, etc.)")
print("  ✓ Prototyping or simple applications")
print("  ✓ Want minimal configuration")
print()
print("Use Manual Config when:")
print("  ✓ Complex URL routing patterns needed")
print("  ✓ Multiple context types with specific URL prefixes")
print("  ✓ Need catch-all patterns")
print("  ✓ Migrating from older versions")
print()
print("Best Practice:")
print("  🎯 Start with auto-generation")
print("  🎯 Add manual config only when needed")
print("  🎯 Both can coexist - manual config takes precedence")
print()
