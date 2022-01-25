from bclib import edge

if "options" not in dir():
    options = {
        "server": {
            "ip": "localhost",
            "port": 1020,
        },
        "router": "web"
    }


app = edge.from_options(options)


@app.web_action(app.callback(lambda x: x.url.endswith("app")))
def process_basiscore_source(context: edge.WebContext):
    return "hi if url end with app"


@app.web_action()
def process_basiscore_source(context: edge.WebContext):
    return "hi (default)"


app.listening()
