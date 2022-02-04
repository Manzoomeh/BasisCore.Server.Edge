import pika
import json
import asyncio


connection = pika.BlockingConnection(
    pika.URLParameters('amqp://guest:guest@localhost:5672'))
channel = connection.channel()
channel.queue_declare(queue='hello')


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    cmd = json.loads(body)
    print(" [x] Received %r" % cmd)
    print(" [x] Received %r" % cmd["key"])


channel.basic_consume(
    queue='hello', on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


async def g():
    await asyncio.sleep(2)
    print("c")
    channel.stop_consuming()
    channel.cancel()
    try:
        channel.close()
    except:
        pass
    try:
        connection.close()
    finally:
        print("eee")


async def co():
    try:
        loop = asyncio.get_running_loop()
        t1 = loop.run_in_executor(None, channel.start_consuming)
        await t1
    except asyncio.CancelledError:
        print("ddddd")
        channel.stop_consuming()
        channel.cancel()
        try:
            channel.close()
        except:
            pass
        try:
            connection.close()
        finally:
            print("eee")


async def ccc(t):
    await asyncio.sleep(2)
    t.cancel()

# loop = asyncio.get_event_loop()
# try:
#     # main()
#     t1 = loop.run_in_executor(None, channel.start_consuming)
#     loop.create_task(g())
#     loop.run_until_complete(asyncio.ensure_future(t1))
# except KeyboardInterrupt:
#     print('Interrupted')

loop = asyncio.get_event_loop()
try:
    # main()
    t1 = loop.create_task(co())
    t2 = loop.create_task(ccc(t1))
    loop.run_until_complete(t1)
except KeyboardInterrupt:
    print('Interrupted')

print("end")
