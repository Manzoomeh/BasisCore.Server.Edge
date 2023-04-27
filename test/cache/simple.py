from bclib import edge
from datetime import datetime


options = {
    "server": "localhost:8080",
    "router": "restful",
    "cache": {
        "type": "memory",
    }
}

app = edge.from_options(options)
data = {
    "data": "static-data",
    "time": datetime.now().strftime("%H:%M:%S")
}

app.cache_manager.add_or_update("demo", data, life_time=None)


@app.restful_action(app.url("api/data"))
def rest_get(context: edge.RESTfulContext):
    print("rest_get")
    return context.dispatcher.cache_manager.get_cache("demo")

@app.restful_action(app.get("api/get/:key"))
def get_data(context: edge.RESTfulContext):
    key = context.url_segments.key
    print(f"GET -> {key}")
    cache_data_list = context.dispatcher.cache_manager.get_cache(key)
    print("cache_data_list: ", cache_data_list)
    return {
        "result": cache_data_list
    } if len(cache_data_list) > 0 else {
        "error": "Key not found in cache dict!"
    }

@app.restful_action(app.post("api/:action/:key"))
def add_new_data(context: edge.RESTfulContext):
    key = context.url_segments.key
    action = context.url_segments.action
    if action in ("add", "set"):
        print(f"{action} -> {key}")
        body = context.body
        if body is not None:
            new_data = body.data
            if new_data is not None:
                life_time = int(body.life_time) if body.has("life_time") else None
                ret_val = {
                    "status": context.dispatcher.cache_manager.add_or_update(key, new_data, life_time)
                } if action == "add" else {
                    "status": context.dispatcher.cache_manager.set_data(key, new_data, life_time)
                }
            else:
                ret_val = {
                    "error": "data not found in body!"
                }
        else:
            ret_val = {
                "error": "body is empty!"
            }
    else:
        ret_val = {
            "error": "invalid action! (add or set)"
        }
    return ret_val

@app.restful_action(app.get("api/clean"))
def clean_cache(context: edge.RESTfulContext):
    print("CLEAND CACHE...")
    return {
        "Status": context.dispatcher.cache_manager.clean()
    }

@app.restful_action(app.post("api/reset"))
def reset_cache(context: edge.RESTfulContext):
    print("RESET CACHE...")
    body = context.body
    if body is not None:
        keys = body.key
        if keys is None or isinstance(keys, list):
            ret_val = {
                "status": context.dispatcher.cache_manager.reset(keys)
            }
        else:
            ret_val = {
                "error": "key object is invalid! (list or None)"
            }
    else:
        ret_val = {
            "error": "body is empty!"
        }
    return ret_val


app.listening()

