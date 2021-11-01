import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='demo')

msg_type = "clear-cache"
keys = ["member-list"]
msg = dict()
msg["type"] = msg_type
msg["keys"] = keys

msg_json = json.dumps(msg)
print(msg_json)
channel.basic_publish(exchange='', routing_key='demo', body=msg_json)
print(f"Sent {msg_type} for [{keys}]")
connection.close()
