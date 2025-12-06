from bclib import edge

USERNAME = "guest"
PASSWORD = "guest"
HOST = "localhost"
PORT = 5672

options = {
    "http": "localhost:8080",
    "router": {
        "restful": [
            "*"
        ],
        "rabbit": [
            {
                "url": f"amqp://{USERNAME}:{PASSWORD}@{HOST}:{PORT}",
                "queue": "Test_Abolfazl",
                "durable": True
            }
        ]
    },
    "settings": {
        "connections.rabbit.demo": {
            "url": f"amqp://{USERNAME}:{PASSWORD}@{HOST}:{PORT}",
            "queue": "Test_Abolfazl",
            "durable": True
        }
    }
}

app = edge.from_options(options)


@app.rabbit_handler()
def process_rabbit_request(context: edge.RabbitContext):
    print(context.message)

@app.restful_handler()
def process_restful_request(context: edge.RESTfulContext):
    db = context.dispatcher.db_manager.open_rabbit_connection("demo")
    with db:
        msg = dict()
        msg["type"] = "message-type-demo"
        msg["keys"] = ["data1", "data2", "data3"]
        db.publish(msg)
    return {
        "status": True
    }


app.listening()
