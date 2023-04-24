from bclib import edge
from datetime import datetime
import time

options = {
    "server": "localhost:8080",
    "router": "restful",
    "cache": {
        "type": "memory",
    }
}

app = edge.from_options(options)


@app.restful_action(app.url("api/data"))
@app.cache("demo", 15)
def rest_get(context: edge.RESTfulContext):
    print("doing...")
    time.sleep(5)
    now = datetime.now()
    ret_val = {
        "data": "static-data",
        "time": now.strftime("%H:%M:%S")
    }
    return ret_val


@app.restful_action(app.url("api/:key/:action"))
def rest_set(context: edge.RESTfulContext):
    # key = "demo"
    print(f"rest_set -> {context.url_segments.action}")
    action = context.url_segments.action
    key = context.url_segments.key
    if action in ("get", "edit"):
        cache_data_list = context.dispatcher.cache_manager.get_cache(key)
        if len(cache_data_list) > 0:
            if action == "get":
                result = []
                for item in cache_data_list:
                    result.append({
                        "data": item.data,
                        "expired": item.is_expired
                    })
                ret_val = {
                    "result": result
                }
            elif action == "edit":
                for item in cache_data_list:
                    cache = item.data
                    cache["data"] += "*"
                    item.update_data(cache)
                ret_val = {
                    "result": "edited"
                }
        else:
            ret_val = {
                "result": "Key not found in cache list!"
            }
    elif action == "reset":
        context.dispatcher.cache_manager.reset_cache([key])
        ret_val = {
            "result": f"Cache related to {key} was reset"
        }
    elif action == "new":
        now = datetime.now()
        new_data = {
            "data": "new-static-data",
            "time": now.strftime("%H:%M:%S")
        }
        ret_val = context.dispatcher.cache_manager.add_or_update_cache_list(key, new_data)
    
    return ret_val


app.listening()
