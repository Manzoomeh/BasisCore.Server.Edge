"""
Demonstration of the new web_handler and restful_handler decorator parameters

This file showcases the convenience parameters added to web_handler and restful_handler:
- route: URL pattern with parameters
- method: Single HTTP method filter
- methods: Multiple HTTP methods filter
- rules: Additional custom predicates
"""

from bclib import edge

options = {
    "server": "localhost:8080",
    "router": {
        "restful": ["/api/*"],
        "web": ["*"]
    }
}

app = edge.from_options(options)


# ============================================================================
# WEB ACTION EXAMPLES
# ============================================================================

# Example 1: Simple route parameter
@app.web_handler("about")
def about_page(context: edge.HttpContext):
    """Simple route with no method restriction"""
    return "<h1>About Us</h1>"


# Example 2: Route with single method
@app.web_handler("contact", method="GET")
def contact_page(context: edge.HttpContext):
    """GET request only"""
    return "<h1>Contact Form</h1>"


@app.web_handler("contact", method="POST")
def submit_contact(context: edge.HttpContext):
    """POST request only"""
    return "<h1>Thank you for contacting us!</h1>"


# Example 3: Route with multiple methods
@app.web_handler("products/:id", method=["GET", "PUT", "DELETE"])
def product_handler(context: edge.HttpContext):
    """Handles GET, PUT, and DELETE for products"""
    product_id = context.url_segments.get('id')
    method = context.cms.get('request', {}).get('methode', 'unknown')
    return f"<h1>Product {product_id} - Method: {method}</h1>"


# Example 4: Route with URL parameters
@app.web_handler("users/:user_id/posts/:post_id")
def user_post(context: edge.HttpContext):
    """Multiple URL parameters"""
    user_id = context.url_segments['user_id']
    post_id = context.url_segments['post_id']
    return f"<h1>User {user_id} - Post {post_id}</h1>"


# Example 5: Using additional predicates with route
@app.web_handler(
    "admin/:section",
    app.has_value("context.query.token"),
    method="GET"
)
def admin_panel(context: edge.HttpContext):
    """Requires token query parameter"""
    section = context.url_segments['section']
    token = context.query.get('token')
    return f"<h1>Admin {section} - Token: {token}</h1>"


# Example 6: Combining route with additional predicates
@app.web_handler(
    "search",
    app.has_value("context.query.q"),
    app.in_list("context.query.type", "user", "post", "product")
)
def search_handler(context: edge.HttpContext):
    """Search with required parameters"""
    query = context.query.get('q')
    search_type = context.query.get('type')
    return f"<h1>Searching {search_type} for: {query}</h1>"


# ============================================================================
# RESTFUL ACTION EXAMPLES
# ============================================================================

# Example 7: Simple RESTful route
@app.restful_handler("api/users")
def list_users(context: edge.RESTfulContext):
    """List all users"""
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }


# Example 8: RESTful route with parameter and method
@app.restful_handler("api/users/:id", method="GET")
def get_user(context: edge.RESTfulContext):
    """Get single user"""
    user_id = context.url_segments['id']
    return {
        "id": user_id,
        "name": f"User {user_id}"
    }


@app.restful_handler("api/users", method="POST")
def create_user(context: edge.RESTfulContext):
    """Create new user"""
    return {
        "status": "created",
        "message": "User created successfully"
    }


# Example 9: RESTful with multiple methods
@app.restful_handler("api/posts/:id", method=["PUT", "PATCH"])
def update_post(context: edge.RESTfulContext):
    """Update post - accepts both PUT and PATCH"""
    post_id = context.url_segments['id']
    return {
        "status": "updated",
        "post_id": post_id
    }


# Example 10: RESTful with additional predicates
@app.restful_handler(
    "api/products/:id",
    app.has_value("context.query.confirm"),
    method="DELETE"
)
def delete_product(context: edge.RESTfulContext):
    """Delete product with confirmation"""
    product_id = context.url_segments['id']
    return {
        "status": "deleted",
        "product_id": product_id
    }


# Example 11: Using traditional predicates (still supported)
@app.restful_handler(
    app.url("api/legacy/:id"),
    app.equal("context.cms.request.methode", "get")
)
def legacy_style(context: edge.RESTfulContext):
    """Traditional predicate style still works"""
    return {"message": "Legacy style works too!"}


# Example 12: Mixing new parameters with traditional predicates
@app.restful_handler(
    "api/orders",
    app.in_list("context.query.status", "active", "pending"),
    method="GET"
)
def filtered_orders(context: edge.RESTfulContext):
    """Mix route parameter with traditional predicates"""
    status = context.query.get('status')
    return {
        "orders": [],
        "filter": status
    }


# Default handlers
@app.web_handler()
def default_web_handler(context: edge.HttpContext):
    """Default handler for unmatched web requests"""
    return """
    <html>
        <head><title>Decorator Parameters Demo</title></head>
        <body>
            <h1>BasisCore Edge - Decorator Parameters Demo</h1>
            <h2>Web Routes:</h2>
            <ul>
                <li><a href="/about">/about</a> - Simple route</li>
                <li><a href="/contact">/contact</a> - GET/POST methods</li>
                <li><a href="/products/123">/products/123</a> - Multiple methods</li>
                <li><a href="/users/1/posts/5">/users/1/posts/5</a> - Multiple params</li>
                <li><a href="/admin/dashboard?token=abc123">/admin/dashboard?token=abc123</a> - With rules</li>
                <li><a href="/search?q=test&type=user">/search?q=test&type=user</a> - Complex rules</li>
            </ul>
            <h2>RESTful API Routes:</h2>
            <ul>
                <li>GET <a href="/api/users">/api/users</a></li>
                <li>GET <a href="/api/users/1">/api/users/1</a></li>
                <li>POST /api/users</li>
                <li>PUT/PATCH <a href="/api/posts/1">/api/posts/1</a></li>
                <li>DELETE /api/products/1?confirm=yes</li>
                <li>GET <a href="/api/legacy/1">/api/legacy/1</a> - Legacy style</li>
                <li>GET <a href="/api/orders?status=active">/api/orders?status=active</a></li>
            </ul>
        </body>
    </html>
    """


@app.restful_handler()
def default_restful_handler(context: edge.RESTfulContext):
    """Default handler for unmatched RESTful requests"""
    return {
        "error": "Not Found",
        "message": "The requested API endpoint does not exist"
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Decorator Parameters Demo - BasisCore Edge Server")
    print("=" * 70)
    print("\nNew decorator parameters available:")
    print("  - route: URL pattern (e.g., 'users/:id')")
    print("  - method: Single HTTP method ('GET', 'POST', etc.)")
    print("  - methods: List of HTTP methods (['GET', 'POST'])")
    print("  - rules: Additional custom predicates")
    print("\nBoth traditional predicates and new parameters can be mixed!")
    print("=" * 70)
    print()

    app.listening()
