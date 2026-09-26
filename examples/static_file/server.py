"""StaticFileHandler serving ./public."""
from pathlib import Path

from bclib import edge
from bclib.utility import StaticFileHandler

SCRIPT_DIR = Path(__file__).parent

app = edge.from_options(
    {
        "name": "static-file",
        "http": "localhost:9180",
        "router": "web",
        "log_error": True,
        "log_request": True,
    }
)

app.add_static_handler(
    StaticFileHandler(
        base_dir=SCRIPT_DIR / "public",
        allowed_extensions={
            ".html",
            ".htm",
            ".css",
            ".js",
            ".json",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".webp",
        },
        enable_index=True,
        index_files=["index.html", "index.htm"],
    )
)


if __name__ == "__main__":
    print("Static files -> http://localhost:9180/")
    app.listening()
