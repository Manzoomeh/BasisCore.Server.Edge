import asyncio
import string
import random
import os
import time
from bclib import edge


options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "defaultRouter": "server_source",
    "router": "web",
    "log_error": True
}

app = edge.from_options(options)


sessions: 'dict[str, asyncio.Future]' = dict()


def f():
    time.sleep(1)
    print('haha')


async def send_data_async(session_id: str):
    id = 1
    print(f'Send data form {session_id} start!')
    while True:
        try:
            await asyncio.sleep(1)
            data = {
                "setting": {
                    "keepalive": True
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
            print(f'Send data form {session_id}')
            await app.send_message_async(
                edge.Message.create_from_object(session_id, data))
        except asyncio.CancelledError:
            print(f'Send data form {session_id} stopped!')
            return
########
# Socket
########


@app.socket_action(app.in_list("context.message_type", edge.MessageType.NOT_EXIST, edge.MessageType.DISCONNECT))
def process_not_exist_message(context: edge.SocketContext):
    print(f'process_not_exist_message for {context.session_id}')
    if context.session_id in sessions:
        future = sessions[context.session_id]
        del sessions[context.session_id]
        future.cancel()
    return True


@app.socket_action(app.in_list("context.message_type", edge.MessageType.CONNECT))
def process_not_connect_message(context: edge.SocketContext):
    print(f'process_not_connect_message for {context.session_id}')
    future = context.dispatcher.run_in_background(
        send_data_async, context.session_id)
    sessions[context.session_id] = future
    return True


@app.socket_action()
def process_all_other_message_async(context: edge.SocketContext):
    print(f"process_all_other_message for {context.session_id}")
    context.dispatcher.run_in_background(f)
    return True


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
