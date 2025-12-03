"""Logger Dependency Injection HTTP Server Example

Demonstrates how to use ILogger[T] for type-safe logger injection in HTTP handlers.
Run this server and access endpoints to see logger in action.
"""
from typing import Optional

from bclib import edge
from bclib.logger import ILogger

# Server configuration
options = {
    "http": "localhost:8080",
    "logger": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

app = edge.from_options(options)


@app.handler("user/login")
async def user_login(
    context: edge.RESTfulContext,
    logger: ILogger[None],
    user_id: Optional[int] = None
):
    """User login endpoint - demonstrates logger injection in handler"""

    logger.info(f"User login attempt %s", user_id)
    logger.debug(
        f"Request headers: {dict(context.cms.get('request', {}).get('headers', {}))}")

    return {
        "status": "success",
        "message": f"User {user_id} logged in successfully",
        "logged": True
    }


@app.restful_handler("db/connect")
async def db_connect(logger: ILogger[None]):
    """Database connection endpoint - demonstrates database operations logging"""
    logger.info("Attempting database connection")

    try:
        # Simulate connection
        logger.debug("Connection parameters validated")
        logger.debug("Connection established to database server")

        return {
            "status": "connected",
            "message": "Database connection successful",
            "database": "production_db"
        }
    except Exception as e:
        logger.exception("Database connection failed")
        return {
            "status": "error",
            "message": str(e)
        }


@app.handler("order/create", method="POST")
async def create_order(
    context: edge.RESTfulContext,
    logger: ILogger[None]
):
    """Order creation endpoint - demonstrates complex operation logging"""
    user_id = context.query.get('user_id')
    items = context.query.get('items', '').split(
        ',') if context.query.get('items') else []

    logger.info(f"Creating order", user_id=user_id, item_count=len(items))
    logger.debug(f"Order items: {items}")

    # Simulate order creation
    order_id = 12345
    logger.info(f"Order created successfully",
                order_id=order_id, user_id=user_id)

    return {
        "status": "success",
        "order_id": order_id,
        "user_id": user_id,
        "items": items,
        "message": "Order created successfully"
    }


@app.restful_handler("order/status")
async def order_status(
    context: edge.RESTfulContext,
    logger: ILogger[None],
    order_id: Optional[int] = None
):
    """Order status endpoint - demonstrates query logging"""

    logger.info(f"Checking order status %s", order_id)
    logger.debug(f"Query parameters: {context.query}")

    return {
        "order_id": order_id,
        "status": "processing",
        "message": "Order is being processed"
    }


@app.web_handler("health")
async def health_check(logger: ILogger[None]):
    """Health check endpoint - demonstrates simple logging"""
    logger.debug("Health check requested")

    return """
    <html>
        <head><title>Health Check</title></head>
        <body>
            <h1>✓ Server is running</h1>
            <p>Logger dependency injection is working!</p>
        </body>
    </html>
    """


@app.web_handler()
async def default_handler(logger: ILogger[None]):
    """Default handler for unmatched routes - demonstrates catch-all logging"""
    logger.info("Serving default page")

    return """
    <html>
        <head><title>Logger DI Example</title></head>
        <body>
            <h1>Logger Dependency Injection HTTP Server</h1>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/user/login?user_id=123">GET /user/login?user_id=123</a> - User login with logger</li>
                <li><a href="/db/connect">GET /db/connect</a> - Database connection with logger</li>
                <li><a href="/order/create?user_id=123&items=item1,item2,item3">POST /order/create</a> - Create order (use POST)</li>
                <li><a href="/order/status?order_id=12345">GET /order/status?order_id=12345</a> - Order status</li>
                <li><a href="/health">GET /health</a> - Health check</li>
            </ul>
            <p>Check console output to see logger messages!</p>
        </body>
    </html>
    """


if __name__ == "__main__":
    print("Starting Logger DI HTTP Server on http://localhost:8082")
    print("Available endpoints:")
    print("  - GET  /user/login?user_id=123")
    print("  - GET  /db/connect")
    print("  - POST /order/create?user_id=123&items=item1,item2")
    print("  - GET  /order/status?order_id=12345")
    print("  - GET  /health")
    print("\nWatch the console for logger output!")

    app.listening()
