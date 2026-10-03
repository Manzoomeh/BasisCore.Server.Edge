"""Docker sample app (wwwroot next to this file)."""
from pathlib import Path

from bclib import edge
from bclib.context import HttpContext

WWW = Path(__file__).resolve().parent / "wwwroot"

options = {
    "name": "docker-sample",
    "http": "0.0.0.0:9181",
    "router": {"web": ["*"]},
    "log_request": True,
}

app = edge.from_options(options)


def read_asset(name: str) -> str:
    path = WWW / name
    return path.read_text(encoding="utf-8")


@app.web_handler(app.url(":file"))
def by_file(context: HttpContext):
    return read_asset(context.url_segments.file)


@app.web_handler()
def index(_: HttpContext):
    return read_asset("index.html")


if __name__ == "__main__":
    print("Docker sample -> http://localhost:9181/")
    app.listening()
