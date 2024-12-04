import asyncio
import string
import random
import os
import time
from bclib import edge
import datetime


options = {
    "endpoint": "127.0.0.1:1025",
    "defaultRouter": "server_source",
    "router": "web",
    "log_error": True
}

app = edge.from_options(options)


sessions: 'dict[str, asyncio.Future]' = dict()


def f():
    time.sleep(1)
    print('haha')


async def send_data_async(context: edge.SocketContext):
    id = 1

    print(f'Send data form {context.message.session_id} start!')
    while True:
        keep_alive = id < 5
        try:
            await asyncio.sleep(1)
            data = {
                "setting": {
                    "keepalive": keep_alive
                },
                "sources": [
                    {
                        "options": {
                            "tableName": "user.list",
                            "keyFieldName": "id",
                            "mergeType": 1,
                        },
                        "data": [
                            {
                                "id": id,
                                "age": random.randint(10, 99),
                                "name": ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
                            },
                        ],
                    },
                ],
            }
            id += 1
            print(
                f'Send data to {context.message.session_id} in {datetime.datetime.now()}')
            try:
                await context.send_object_async(data)
            except:  # ConnectionError
                print("connection closed!")
                return
            if not keep_alive:
                return
        except asyncio.CancelledError:
            print(
                f'Send data to {context.message.session_id} stopped in {datetime.datetime.now()}!')
            return
########
# Socket
########


@app.socket_action()
async def process_message_async(context: edge.SocketContext):
    print(
        f'message of type {context.message.type} come from {context.message.session_id} in {datetime.datetime.now()}')
    msg = await context.read_message_async()
    print(
        f'message of type {msg.type} come from {msg.session_id} in {datetime.datetime.now()}')
    future = context.dispatcher.run_in_background(
        send_data_async, context)
    while not future.done():
        try:
            msg = await context.read_message_async()
            print(
                f'message of type {msg.type} come from {msg.session_id} in {datetime.datetime.now()}')
            if msg.type in [edge.MessageType.DISCONNECT, edge.MessageType.NOT_EXIST]:
                break
        except Exception as ex:
            print("connection closed!",ex)
            break
    future.cancel()


#####
# Web
#####
@app.web_action()
def process_web_message(_: edge.WebContext):
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "list-data.html")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


app.listening()
