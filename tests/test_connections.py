"""Connection DI resolution without opening real network sockets."""
from bclib.connections.mongo import IMongoConnection
from bclib.connections.mongo.mongo_connection import MongoConnection
from bclib.connections.rabbit import IRabbitConnection
from bclib.connections.rabbit.rabbit_connection import RabbitConnection
from bclib.connections.restful import IRestfulConnection
from bclib.connections.restful.restful_connection import RestfulConnection


def test_resolve_mongo_connection_without_client(connected_app):
    db = connected_app.service_provider.get_service(
        IMongoConnection["database.users"]
    )
    assert isinstance(db, MongoConnection)
    assert db._options["connection_string"].startswith("mongodb://")
    assert db._options["database_name"] == "users_db"
    assert db._client is None


def test_resolve_rabbit_connection_without_connect(connected_app):
    rabbit = connected_app.service_provider.get_service(
        IRabbitConnection["rabbitmq.tasks"]
    )
    assert isinstance(rabbit, RabbitConnection)
    assert rabbit._url.startswith("amqp://")
    assert rabbit.queue_name == "task_queue"
    assert rabbit._connection is None


def test_resolve_restful_connection_without_session(connected_app):
    api = connected_app.service_provider.get_service(
        IRestfulConnection["external_api"]
    )
    assert isinstance(api, RestfulConnection)
    assert api.base_url == "https://api.example.com"
    assert api.timeout == 30
