import pika
import sys
import os
import json


def main():
    connection = pika.BlockingConnection(
        pika.URLParameters('amqp://guest:guest@localhost:5672'))
    channel = connection.channel()

    #channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)
        #cmd = json.loads(body)
        #print(" [x] Received %r" % cmd)
        
        #print(" [x] Received %r" % cmd["key"])

    channel.basic_consume(
        queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
