"""Unhandled exception -> error response demo."""
from bclib import edge
from bclib.context import HttpContext

options = {
    "name": "ex-simple",
    "http": "localhost:9143",
    "router": "web",
    "log_error": True,
}

app = edge.from_options(options)


@app.web_handler()
def process_default(_: HttpContext):
    return 1 / 0  # intentional


if __name__ == "__main__":
    print("Unhandled error -> http://localhost:9143/")
    app.listening()
