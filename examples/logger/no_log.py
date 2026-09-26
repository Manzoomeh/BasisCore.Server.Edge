"""Quiet REST sample (log_request disabled)."""
from bclib import edge
from bclib.context import RESTfulContext

options = {
    "name": "logger-no-log",
    "http": "localhost:9152",
    "router": "restful",
    "log_request": False,
}

app = edge.from_options(options)


@app.restful_handler()
async def process_restful_request(_: RESTfulContext):
    return {"result": "ok", "logged_request": False}


if __name__ == "__main__":
    print("No-log REST -> http://localhost:9152/")
    app.listening()
