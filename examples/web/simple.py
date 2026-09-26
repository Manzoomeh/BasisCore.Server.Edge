"""Minimal web handlers."""
from bclib import edge
from bclib.context import HttpContext
from bclib.logger import ILogger

options = {
    "name": "web-simple",
    "http": "localhost:9182",
    "router": "web",
    "log_error": True,
}

app = edge.from_options(options)


@app.web_handler("hello", method="GET")
def hello(_: HttpContext):
    return "<h1>Hello from web-simple</h1>"


@app.web_handler()
def default(context: HttpContext, logger: ILogger["WebSimple"]):
    logger.info("default web handler for %s", context.url)
    return f"<p>default handler for <code>{context.url}</code></p>"


if __name__ == "__main__":
    print("Web simple -> http://localhost:9182/hello")
    app.listening()
