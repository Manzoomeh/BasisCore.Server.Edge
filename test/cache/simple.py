from bclib import edge
from datetime import datetime


options = {
    "server": "localhost:8080",
    "router": "restful",
    "cache": {
        "type": "memory",
        "clean_interval": 60, # 1 Minute
        "reset_interval": 120 # 2 Minutes
    }
}

app = edge.from_options(options)
data = {
    "data": "static-data",
    "time": datetime.now().strftime("%H:%M:%S")
}

app.cache_manager.add_or_update("demo", data, life_time=300)

@app.restful_handler(
    app.get("api/data/:key")
)
def rest_get(context: edge.RESTfulContext):
    key = context.url_segments.key
    print(f"get data for key='${key}'")
    return {
        "From Cache": context.dispatcher.cache_manager.get_cache(key)
    }

@app.restful_handler(
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

@app.restful_handler(
    app.post("api/clean")
)
def clean_cache(context: edge.RESTfulContext):
    print("Cleaning Cache...")
    return {
        "Status": context.dispatcher.cache_manager.clean()
    }

app.listening()

