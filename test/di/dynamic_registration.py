"""
Dynamic Handler Registration Example

Shows how to register handlers at runtime without decorators.
Useful for plugin systems, dynamic APIs, or configuration-based routing.
"""
from bclib import edge
from bclib.context import RESTfulContext


# Define handlers as regular functions
def get_users_handler(context: RESTfulContext):
    """Get list of users"""
    users = [
        {"id": 1, "name": "Ali"},
        {"id": 2, "name": "Sara"}
    ]
    return {"users": users}


def get_user_handler(context: RESTfulContext):
    """Get single user by ID"""
    user_id = context.url_segments.get("id", "1")
    return {
        "user": {
            "id": user_id,
            "name": f"User {user_id}"
        }
    }


def create_user_handler(context: RESTfulContext):
    """Create new user"""
    return {
        "message": "User created",
        "user": {"id": 3, "name": "New User"}
    }


def health_check_handler():
    """Health check endpoint - no context needed"""
    return {"status": "ok", "service": "BasisCore Edge"}


# Setup
options = {
    "server": "localhost:8098",
    "router": "restful",
    "log_errors": True
}

app = edge.from_options(options)

print("=" * 70)
print("Dynamic Handler Registration")
print("=" * 70)
print()

# Register handlers programmatically (without decorators)
# This is useful for:
# - Loading handlers from configuration
# - Plugin systems
# - Dynamic API generation
# - Conditional handler registration

app.register_handler(
    RESTfulContext,
    get_users_handler,
    [app.url("api/users")]
)

app.register_handler(
    RESTfulContext,
    get_user_handler,
    [app.url("api/users/:id")]
)

app.register_handler(
    RESTfulContext,
    create_user_handler,
    [app.url("api/users"), app.is_post()]
)

app.register_handler(
    RESTfulContext,
    health_check_handler,
    [app.url("health")]
)

print("✓ Handlers registered programmatically")
print()

# You could also load handlers from a configuration file:
"""
handlers_config = [
    {
        "path": "api/users",
        "handler": "get_users_handler",
        "method": "GET"
    },
    {
        "path": "api/users/:id", 
        "handler": "get_user_handler",
        "method": "GET"
    }
]

for config in handlers_config:
    handler_func = globals()[config["handler"]]
    app.register_handler(
        RESTfulContext,
        handler_func,
        [app.url(config["path"])]
    )
"""

print("=" * 70)
print("Benefits of register_handler:")
print("=" * 70)
print("1. No decorators needed - handlers are pure functions")
print("2. Dynamic registration at runtime")
print("3. Easy to load from configuration files")
print("4. Perfect for plugin systems")
print("5. Conditional registration based on settings")
print("6. Can mix with decorator-based handlers")
print()

print("=" * 70)
print("Example Use Cases:")
print("=" * 70)
print("• Load API routes from JSON/YAML config")
print("• Plugin system - load handlers from external modules")
print("• A/B testing - conditionally register different handlers")
print("• Multi-tenant - register tenant-specific handlers")
print("• Feature flags - enable/disable endpoints dynamically")
print()

print("=" * 70)
print()
print("Server URL: http://localhost:8098")
print()
print("Available Endpoints:")
print("  GET  http://localhost:8098/api/users")
print("  GET  http://localhost:8098/api/users/1")
print("  POST http://localhost:8098/api/users")
print("  GET  http://localhost:8098/health")
print()
print("=" * 70)
print()

app.listening()
