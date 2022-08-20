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
ret_val = {
    "data": "static-data",
    "time": datetime.now().strftime("%H:%M:%S")
}

app.cache_manager.add_or_update_cache("demo", ret_val)


@app.restful_action(app.url("api/data"))
def rest_get(context: edge.RESTfulContext):
    print("rest_get")
    return context.dispatcher.cache_manager.get_cache("demo")


@app.restful_action(app.url("api/:action"))
def rest_set(context: edge.RESTfulContext):
    print(f"rest_set -> {context.url_segments.action}")
    ret_val = {
        "result": "ok"
    }
    action = context.url_segments.action
    key = "demo"
    if action == "get":
        cache_data_list = context.dispatcher.cache_manager.get_cache(key)
        ret_val["result"] = cache_data_list
    elif action == "edit":
        cache_data_list = context.dispatcher.cache_manager.get_cache(key)
        cache_data = cache_data_list[0]
        cache_data["data"] += "*"
    elif action == "replace":
        now = datetime.now()
        new_data = {
            "data": "new-static-data",
            "time": now.strftime("%H:%M:%S")
        }
        context.dispatcher.cache_manager.update_cache(key, new_data)
    elif action == "remove":
        context.dispatcher.cache_manager.reset_cache([key])

    return ret_val


app.listening()
