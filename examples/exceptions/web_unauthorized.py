"""UnauthorizedErr from a web callback predicate."""
from bclib import edge
from bclib.context import HttpContext
from bclib.exception import UnauthorizedErr

options = {
    "name": "ex-web-unauth",
    "http": "localhost:9145",
    "router": "web",
}

app = edge.from_options(options)


async def check_url(context: HttpContext) -> bool:
    if context.url.endswith("error"):
        raise UnauthorizedErr("Custom Unauthorize message")
    return True


async def starts_with_app(context: HttpContext) -> bool:
    return context.url.startswith("app")


@app.web_handler(app.callback(starts_with_app), app.callback(check_url))
def process_app(_: HttpContext):
    return "result from process_web_handler"


@app.web_handler()
def process_default(_: HttpContext):
    return "result from process_default_web_handler"


if __name__ == "__main__":
    print("Web unauthorized -> http://localhost:9145/app/error")
    app.listening()
