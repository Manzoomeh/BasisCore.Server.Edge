"""
Dynamic Handler Management Example

Shows how to register/unregister handlers at runtime.
Useful for feature flags, A/B testing, hot-reloading, etc.
"""
from bclib import edge
from bclib.context import RESTfulContext

# Feature flags
FEATURES = {
    "new_api": True,
    "legacy_api": False,
}


# Different versions of handlers
def get_users_v1(context: RESTfulContext):
    """Legacy version - simple list"""
    return {
        "version": "v1",
        "users": ["Ali", "Sara", "Reza"]
    }


def get_users_v2(context: RESTfulContext):
    """New version - detailed info"""
    return {
        "version": "v2",
        "users": [
            {"id": 1, "name": "Ali", "active": True},
            {"id": 2, "name": "Sara", "active": True},
            {"id": 3, "name": "Reza", "active": False}
        ]
    }


def maintenance_handler(context: RESTfulContext):
    """Maintenance mode handler"""
    return {
        "status": "maintenance",
        "message": "Service temporarily unavailable"
    }


# Setup
options = {
    "server": "localhost:8099",
    "router": "restful",
    "log_errors": True
}

app = edge.from_options(options)

print("=" * 70)
print("Dynamic Handler Management")
print("=" * 70)
print()


# Register initial handlers based on feature flags
def register_api_handlers():
    """Register API handlers based on feature flags"""

    if FEATURES.get("new_api"):
        print("✓ Registering NEW API (v2)")
        app.register_handler(
            RESTfulContext,
            get_users_v2,
            [app.url("api/users")]
        )
    elif FEATURES.get("legacy_api"):
        print("✓ Registering LEGACY API (v1)")
        app.register_handler(
            RESTfulContext,
            get_users_v1,
            [app.url("api/users")]
        )
    else:
        print("✓ Registering MAINTENANCE mode")
        app.register_handler(
            RESTfulContext,
            maintenance_handler,
            [app.url("api/users")]
        )


register_api_handlers()


# Admin endpoint to switch versions
@app.restful_handler(app.url("admin/switch/:version"))
async def switch_version(context: RESTfulContext):
    """Admin endpoint to switch API versions dynamically"""
    version = context.url_segments.get("version", "v1")

    # Unregister current handler
    app.unregister_handler(RESTfulContext)  # Remove all

    # Register new handler
    if version == "v1":
        app.register_handler(
            RESTfulContext,
            get_users_v1,
            [app.url("api/users")]
        )
        FEATURES["new_api"] = False
        FEATURES["legacy_api"] = True
    elif version == "v2":
        app.register_handler(
            RESTfulContext,
            get_users_v2,
            [app.url("api/users")]
        )
        FEATURES["new_api"] = True
        FEATURES["legacy_api"] = False
    elif version == "maintenance":
        app.register_handler(
            RESTfulContext,
            maintenance_handler,
            [app.url("api/users")]
        )
        FEATURES["new_api"] = False
        FEATURES["legacy_api"] = False

    return {
        "message": f"Switched to {version}",
        "features": FEATURES
    }


print()
print("=" * 70)
print("Use Cases:")
print("=" * 70)
print("• Feature Flags - Enable/disable features dynamically")
print("• A/B Testing - Switch between different implementations")
print("• Hot Reload - Update handlers without restart")
print("• Maintenance Mode - Temporarily replace all handlers")
print("• Version Migration - Gradual API version migration")
print("• Conditional Routing - Based on time, load, etc.")
print()

print("=" * 70)
print()
print("Server URL: http://localhost:8099")
print()
print("Available Endpoints:")
print("  GET  http://localhost:8099/api/users")
print("       (Currently using v2 API)")
print()
print("Admin Endpoints (switch versions dynamically):")
print("  GET  http://localhost:8099/admin/switch/v1")
print("  GET  http://localhost:8099/admin/switch/v2")
print("  GET  http://localhost:8099/admin/switch/maintenance")
print()
print("Try:")
print("  1. curl http://localhost:8099/api/users")
print("  2. curl http://localhost:8099/admin/switch/v1")
print("  3. curl http://localhost:8099/api/users  (now v1!)")
print("  4. curl http://localhost:8099/admin/switch/maintenance")
print("  5. curl http://localhost:8099/api/users  (maintenance!)")
print()
print("=" * 70)
print()

app.listening()
