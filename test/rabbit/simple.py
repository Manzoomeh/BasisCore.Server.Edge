import edge


options = {
    "server": "localhost:8080",
    "router": {
        "restful": [
            "*"
        ],
        "rabbit": [
            {
                "url": "amqp://guest:guest@localhost:5672",
                "queue": "demo"
            }
        ]
    },
    "settings": {
        "connections.rabbit.demo": {
            "host": "amqp://guest:guest@localhost:5672",
            "queue": "demo"
        }
    }
}

app = edge.from_options(options)


@app.rabbit_action()
def process_rabbit_request(context: edge.RabbitContext):
    print("process_rabbit_request")
    print(context.host, context.message)


@app.restful_action()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    db = context.dispatcher.db_manager.open_rabbit_connection("demo")
    with db:
        msg = dict()
        msg["type"] = "message-type-demo"
        msg["keys"] = ["data1", "data2", "data3"]
        db.publish(msg)
    return True


app.listening()
