"""Logger DI — inject ILogger into handlers."""
from typing import Optional

from bclib import edge
from bclib.context import RESTfulContext, HttpContext
from bclib.logger import ILogger

options = {
    "name": "logger-di",
    "http": "localhost:9150",
    "logger": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

app = edge.from_options(options)


@app.restful_handler("user/login", method="GET")
async def user_login(context: RESTfulContext, logger: ILogger[None]):
    user_id = context.query.get("user_id", "guest")
    logger.info("User login attempt %s", user_id)
    return {"status": "success", "user_id": user_id}


@app.restful_handler("db/connect", method="GET")
async def db_connect(logger: ILogger[None]):
    logger.info("Attempting database connection")
    return {"status": "connected", "database": "demo_db"}


@app.web_handler("health")
async def health_check(logger: ILogger[None]):
    logger.debug("Health check requested")
    return "<h1>OK</h1>"


@app.web_handler()
async def home(_: HttpContext, logger: ILogger[None]):
    logger.info("Serving home")
    return "<p>Logger DI — try /user/login?user_id=1 or /health</p>"


if __name__ == "__main__":
    print("Logger DI -> http://localhost:9150/user/login?user_id=1")
    app.listening()
