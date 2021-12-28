import context
import dispatcher


options = {
    "sender": {
        "ip": "127.0.0.1",
        "port": 1025,
    },
    "receiver": {
        "ip": "127.0.0.1",
        "port": 1026,
    },
    "router": {
        "web": ["*"]
    }
}


app = dispatcher.DuplexSocketDispatcher(options)


# @ app.rabbit_action(app.equal("context.message.type", "clear-cache1"))
# def process_rabbit_message1(context: context.RabbitContext):
#     print("process_rabbit_message1", context.host,
#           context.queue, context.message)


@ app.web_action()
def process_rabbit_message2(context: context.web_context):
    print("process_rabbit_message2")
    # time.sleep(2)
    return "<h1>hi</h1>"


app.listening()
