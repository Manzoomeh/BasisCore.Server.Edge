"""Predicate callback sample."""
from bclib import edge
from bclib.context import HttpContext

options = {
    "name": "predicates-callback",
    "http": "localhost:9120",
    "router": "web",
}

app = edge.from_options(options)


async def is_admin_path(context: HttpContext) -> bool:
    return "admin" in context.url


@app.web_handler(app.callback(is_admin_path))
def admin(context: HttpContext):
    return "admin area"


@app.web_handler()
def other(context: HttpContext):
    return "public area"


if __name__ == "__main__":
    print("Predicates -> http://localhost:9120/admin")
    app.listening()
