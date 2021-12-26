import context
import dispatcher


options = {
    "ip": "127.0.0.1",
    "port": 1025,
    "router": {
        "rabbit": [
          {
              "url": "amqp://guest:guest@localhost:5672",
              "queue": "hello"
          }
        ]
    }
}


app = dispatcher.SocketDispatcher(options)


@ app.rabbit_action(app.equal("context.message.type", "clear-cache1"))
def process_rabbit_message1(context: context.RabbitContext):
    print("process_rabbit_message1", context.host,
          context.queue, context.message)


@ app.rabbit_action()
def process_rabbit_message2(context: context.RabbitContext):
    print("process_rabbit_message2", context.host,
          context.queue, context.message.type)


app.listening()
