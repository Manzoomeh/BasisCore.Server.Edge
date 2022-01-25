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


app.listening()
