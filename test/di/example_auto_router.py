"""Example: Auto-generated router without config"""
import os
import sys

from bclib import edge

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


# ✨ No router configuration needed!
# Router will be auto-generated from registered handlers
options = {
    "server": "localhost:8080"
}

app = edge.from_options(options)

# Register handlers - router is built automatically


@app.restful_action(app.url("api/users"))
async def get_users():
    """Get all users"""
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }


@app.restful_action(app.url("api/users/:user_id"))
async def get_user(user_id: str):
    """Get user by ID"""
    return {
        "user": {"id": user_id, "name": "Alice"}
    }


@app.restful_action(app.url("api/posts"))
async def get_posts():
    """Get all posts"""
    return {
        "posts": [
            {"id": 1, "title": "First Post"},
            {"id": 2, "title": "Second Post"}
        ]
    }


@app.web_action(app.url("index.html"))
async def get_index():
    """Serve home page"""
    return "<html><body><h1>Welcome to BasisCore</h1><p>Auto-generated router example</p></body></html>"


@app.web_action(app.url("about.html"))
async def get_about():
    """Serve about page"""
    return "<html><body><h1>About</h1><p>This is a demonstration of web_action with auto-generated router</p></body></html>"

print("✨ Router Auto-Generation Example")
print("=" * 50)
print()
print("Configuration:")
print(f"  Server: {options['server']}")
print(f"  Router: Auto-generated from handlers")
print()
print("Registered Handlers:")
print("  - GET api/users")
print("  - GET api/users/{user_id}")
print("  - GET api/posts")
print("  - WEB index.html")
print("  - WEB about.html")
print()
print("✅ Router will be automatically generated on startup")
print("   (RESTful handlers → 'restful', Web handlers → 'web')")
print()
print("Benefits:")
print("  • No manual router configuration needed")
print("  • Router adapts to registered handlers")
print("  • Less boilerplate code")
print("  • Automatic context type detection")
print("  • Pattern-based routing for multiple contexts")
print("  • Router initialized before server starts")
print()
print("Note: You can still use manual router config for")
print("      advanced routing patterns if needed.")
print()

# Router will be auto-initialized in listening() → initialize_task()
app.listening()
