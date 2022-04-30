import os
from bclib import edge
from web_push import WebPush
from datetime import datetime

options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "router": {
        "restful": ["/api"],
        "web": ["*"]
    },
    "log_request": True,
    "log_error": True,
    "push": {
        "vapid": {
            "subject": "mailto:mail@example.com",
            "public_key": "BDeRNwAPgVtNfsvZrRrAkm-O4-P36gSDLxDx25gQ-hoXjpdg3MQ8E3_kzZQSEH58ugL5F5Pi-3nKFvtys8R4eys",
            "private_key": "2wsZwjm-dmGZ9O50BVPC0NuERD_wnPvFCS75JXJKF8k"
        }
    }
}

app = edge.from_options(options)

push = WebPush(options)


@app.restful_action(app.url("api/push/add-subscriber"))
def add_subscriber_handler(context: edge.RESTfulContext):
    edge.HttpHeaders.add_cors_headers(context)
    push.add_subscriber(context.body.client, context.body.endpoint,
                        context.body.p256dh, context.body.auth)
    return True


@app.restful_action(app.url("api/push/:type/:client"))
def push_handler(context: edge.RESTfulContext):
    return push.push_object(context.url_segments.client, context.url_segments.type,
                            context.body, "hi", "http://localhost:3000")


@app.restful_action(app.url("api/push/test"))
def test_push_handler(_: edge.RESTfulContext):
    now = datetime.now()
    data = {
        "hh": now.hour,
        "mm": now.minute,
        "ss": now.second,
        "ms": now.microsecond
    }
    return push.push_object("qam-1", "test",
                            data, "hi", "http://localhost:3000")


@app.web_action(app.url("basiscore-serviceWorker.js"))
def sw_js_handler(context: edge.WebContext):
    context.mime = edge.HttpMimeTypes.JS
    return readAsset("basiscore-serviceWorker.js")


@app.web_action(app.url("basiscore.js"))
def bc_js_handler(context: edge.WebContext):
    context.mime = edge.HttpMimeTypes.JS
    return readAsset("basiscore.js")


@app.web_action()
def default_handler(context: edge.WebContext):
    return readAsset("index.html").replace("___PUBLIK_KEY___", context.dispatcher.options.push.vapid.public_key)


def readAsset(assetName: str) -> str:
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), f"wwwroot/{assetName}")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


app.listening()
