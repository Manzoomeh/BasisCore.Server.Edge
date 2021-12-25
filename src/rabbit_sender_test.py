import json
import pika

connection = pika.BlockingConnection(
    pika.URLParameters('amqp://guest:guest@localhost:5672'))
channel = connection.channel()

channel.queue_declare(queue='demo')

MSG_TYPE = "clear-cache"
keys = ["member-list"]
msg = dict()
msg["type"] = MSG_TYPE
msg["keys"] = keys

msg_json = json.dumps(msg)
print(msg_json)
channel.basic_publish(exchange='', routing_key='demo', body=msg_json)
print(f"Sent {MSG_TYPE} for [{keys}]")
connection.close()
