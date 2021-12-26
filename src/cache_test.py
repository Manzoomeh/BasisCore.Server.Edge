from dispatcher import SocketDispatcher
from context import RESTfulContext
from datetime import datetime


options = {
    "ip": "127.0.0.1",
    "port": 1025,
    "router": {
        "restful": ["api/"],
    },
    "cache": {
        "type": "memory",
    }
}

app = SocketDispatcher(options)


@app.restful_action(app.url("api/data"))
@app.cache(15, "demo")
def rest_get(context: RESTfulContext):
    print("rest_get")
    now = datetime.now()

    ret_val = {
        "data": "static-data",
        "time": now.strftime("%H:%M:%S")
    }
    return ret_val


@app.restful_action(app.url("api/:action"))
def rest_set(context: RESTfulContext):
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
