from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web",
        "log_error": True,
        "log_request": True
    }


app = edge.from_options(options)


app.listening()
