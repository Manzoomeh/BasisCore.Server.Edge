"""Minimal HTTP/web server with a callback predicate."""
from bclib import edge
from bclib.context import HttpContext

options = {
    "name": "http-simple",
    "http": "localhost:9110",
    "router": "web",
}

app = edge.from_options(options)


async def ends_with_app(context: HttpContext) -> bool:
    return context.url.endswith("app")


@app.web_handler(app.callback(ends_with_app))
def process_app(context: HttpContext):
    return "result from process_app handler"


@app.web_handler()
def process_default(context: HttpContext):
    return f"default web handler for url={context.url}"


if __name__ == "__main__":
    print("HTTP simple -> http://localhost:9110/")
    app.listening()
