from bclib import edge
from datetime import datetime


options = {
    "server": "localhost:8080",
    "router": "restful",
    "cache": {
        "type": "initial_memory",
    }
}

app = edge.from_options(options)


@app.cache(key="demo1,demo2")
def set_cache():
    print("set_cache")
    now = datetime.now()

    demo1_val = {
        "data": "static-data1",
        "time": now.strftime("%H:%M:%S")
    }
    demo2_val = {
        "data": "static-data2",
        "time": now.strftime("%H:%M:%S")
    }
    return demo1_val, demo2_val


@app.restful_action(app.url("api/:action"))
def rest_set(context: edge.RESTfulContext):
    print(f"rest_set -> {context.url_segments.action}")
    now = datetime.now()
    ret_val = {
        "result": "ok"
    }
    action = context.url_segments.action
    key = "demo1"
    if action == "get":
        cache_data_list = context.dispatcher.cache_manager.get_cache(key)
        ret_val["result"] = cache_data_list
    elif action == "hget":
        sub_key = context.body["sub_key"]
        cache_data_list = context.dispatcher.cache_manager.hget_cache(key, sub_key)
        ret_val["result"] = cache_data_list
    elif action == "update":
        new_data = context.body
        cache_data_list = context.dispatcher.cache_manager.update_cache(key, new_data)

    elif action == "hupdate":
        sub_key = context.body["sub_key"]
        new_data = now.strftime("%H:%M:%S")
        context.dispatcher.cache_manager.hupdate_cache(key, sub_key, new_data)

    return ret_val


app.listening()
