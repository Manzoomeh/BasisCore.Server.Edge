import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

d = dict()
d["type"] = "clear-cache"
d["key"] = "rrr"

j = json.dumps(d)
print(j)
channel.basic_publish(exchange='', routing_key='hello', body=j)
print(" [x] Sent 'Hello World!'")
connection.close()
