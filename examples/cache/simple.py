"""In-memory cache manager demo."""
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext

options = {
    "name": "cache-simple",
    "http": "localhost:9160",
    "router": "restful",
    "cache": {
        "type": "memory",
        "clean_interval": 60,
        "reset_interval": 120,
    },
}

app = edge.from_options(options)
app.cache_manager.add_or_update(
    "demo",
    {"data": "static-data", "time": datetime.now().strftime("%H:%M:%S")},
    life_time=300,
)


@app.restful_handler(app.get("api/data/:key"))
def rest_get(context: RESTfulContext):
    key = context.url_segments["key"]
    return {"From Cache": context.dispatcher.cache_manager.get_cache(key)}


@app.restful_handler(app.post("api/:action"))
def action_api(context: RESTfulContext):
    action = context.url_segments["action"]
    body = context.body
    if action == "add" and body is not None:
        key = body.get("key") if isinstance(body, dict) else getattr(body, "key", None)
        value = body.get("value") if isinstance(body, dict) else getattr(body, "value", None)
        if key is not None:
            context.dispatcher.cache_manager.add_or_update(key, value, life_time=300)
            return {"Status": True, "key": key}
    if action == "reset":
        context.dispatcher.cache_manager.reset()
        return {"Status": True}
    return {"Status": False, "action": action}


@app.restful_handler()
def home(_: RESTfulContext):
    return {
        "endpoints": [
            "GET /api/data/demo",
            "POST /api/add  {\"key\":\"k\",\"value\":{...}}",
            "POST /api/reset",
        ]
    }


if __name__ == "__main__":
    print("Cache simple -> http://localhost:9160/api/data/demo")
    app.listening()
