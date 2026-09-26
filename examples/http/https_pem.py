"""HTTPS with PEM cert/key (certs next to this folder)."""
from pathlib import Path

from bclib import edge
from bclib.context import HttpContext

_CERTS = Path(__file__).resolve().parent / "certs"

options = {
    "name": "http-ssl",
    "http": {
        "endpoint": "localhost:9111",
        "ssl": {
            "certfile": str(_CERTS / "server.cert"),
            "keyfile": str(_CERTS / "server.key"),
        },
    },
    "router": "web",
}

app = edge.from_options(options)


@app.web_handler()
def home(context: HttpContext):
    return "<h1>HTTPS OK</h1>"


if __name__ == "__main__":
    print("HTTPS PEM -> https://localhost:9111/")
    app.listening()
