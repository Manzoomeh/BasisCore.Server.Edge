from bclib import edge
from datetime import datetime
import time

options = {
    "server": "localhost:8080",
    "router": "restful",
    "cache": {
        "type": "memory",
        "clean_interval": 0, # 1 Minute
        "reset_interval": 0 # 2 Minutes
    }
}

app = edge.from_options(options)

@app.restful_action(
    app.get("api/data")
)
@app.cache(30, "demo")
def data(context: "edge.RESTfulContext"):
    print("Doing function...")
    time.sleep(2)
    return {
        "data": "static-data",
        "time": datetime.now().strftime("%H:%M:%S")
    }


@app.restful_action(
    app.get("api/get/:key")
)
def get_data(context: edge.RESTfulContext):
    key = context.url_segments.key
    print(f"GET -> {key}")
    return {
        "From Cache": context.dispatcher.cache_manager.get_cache(key)
    }


@app.restful_action(
    app.post("api/:action")
)
def action_api(context: edge.RESTfulContext):
    action = context.url_segments.action
    if action in ("add", "reset"):
        body = context.body
        if body is not None:
            key = body.key # list[str]
            if key is not None:
                print(f"${action} -> ${key}")
                if action == "reset":
                    if isinstance(key, list):
                        return {
                            "Status": context.dispatcher.cache_manager.reset(key)
                        }
                    else:
                        ret_val = {
                            "Error": "key must be a list!"
                        }
                else:
                    new_data = body.data
                    if new_data is not None:
                        life_time = int(body.life_time) if body.has("life_time") else 0
                        ret_val = {
                            "Status": context.dispatcher.cache_manager.add_or_update(key, new_data, life_time)
                        }
                    else:
                        ret_val = {
                            "Error": "data not found in body!"
                        }
            else:
                if action == "reset":
                    print("reset -> all")
                    return {
                        "Status": context.dispatcher.cache_manager.reset()
                    }
                ret_val = {
                    "Error": "key not found in body!"
                }
        else:
            if action == "reset":
                print("reset -> all")
                return {
                    "Status": context.dispatcher.cache_manager.reset()
                }
            else:
                ret_val = {
                    "Error": "body is empty!"
                }
    else:
        ret_val = {
            "Error": "invalid action! (add or reset)"
        }
    return ret_val

@app.restful_action(
    app.post("api/clean")
)
def clean_cache(context: edge.RESTfulContext):
    print("Cleaning Cache...")
    return {
        "Status": context.dispatcher.cache_manager.clean()
    }

app.listening()