"""Restful implementation of Db wrapper"""
import json
from typing import Any
from bclib.utility import DictEx
from ..db_manager.db import Db


class RabbitConnection(Db):
    """Restful implementation of Db wrapper"""

    def __init__(self, connection_setting: DictEx) -> None:
        super().__init__()
        self.__connection_setting = connection_setting
        self.__connection = None
        self.__channel = None

    def __enter__(self):
        import pika
        connection = pika.BlockingConnection(
            pika.URLParameters(self.__connection_setting.host))
        self.__channel = connection.channel()
        self.__channel.queue_declare(queue=self.__connection_setting.queue,
                                     passive=self.__connection_setting.passive if self.__connection_setting.passive else False,
                                     durable=self.__connection_setting.durable if self.__connection_setting.durable else False,
                                     exclusive=self.__connection_setting.exclusive if self.__connection_setting.exclusive else False,
                                     auto_delete=self.__connection_setting.auto_delete if self.__connection_setting.auto_delete else False
                                     )

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__connection is not None:
            self.__connection.close()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def publish(self, message: Any):
        """Send message to rabbit-mq"""
        if self.__channel is not None:
            msg_json = json.dumps(message)
            self.__channel.basic_publish(
                exchange='', routing_key=self.__connection_setting.queue, body=msg_json)
        else:
            raise Exception(f'for host {0}:{1}, channel not created!' %
                            self.__connection_setting.host, self.__connection_setting.queue)
