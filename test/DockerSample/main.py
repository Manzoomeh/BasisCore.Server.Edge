import os
from bclib import edge

options = {
    "server": "0.0.0.0:8080",
    "router": {
        "web": ["*"]
    },
    "log_request": True,
}

app = edge.from_options(options)


@app.web_action(app.url(":file"))
def handler(context: edge.WebContext):
    return readAsset(context.url_segments.file)


@app.web_action()
def handler(context: edge.WebContext):
    return readAsset("index.html")


def readAsset(asset_name: str) -> str:
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), f"wwwroot/{asset_name}")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


app.listening()
