"""HTTPS with PFX certificate."""
from pathlib import Path

from bclib import edge
from bclib.context import HttpContext

_CERTS = Path(__file__).resolve().parent / "certs"

options = {
    "name": "http-ssl-pfx",
    "http": {
        "endpoint": "localhost:9112",
        "ssl": {
            "pfxfile": str(_CERTS / "server.pfx"),
            "password": "1234",
        },
    },
    "router": "web",
}

app = edge.from_options(options)


@app.web_handler()
def home(context: HttpContext):
    return "<h1>HTTPS PFX OK</h1>"


if __name__ == "__main__":
    print("HTTPS PFX -> https://localhost:9112/")
    app.listening()
