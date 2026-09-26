"""Options / AppOptions / IOptions[T] coverage."""
from bclib.options import AppOptions, IOptions


def test_app_options_root(connected_app):
    root = connected_app.service_provider.get_service(AppOptions)
    assert root["name"] == "pytest-connections"
    assert "database" in root


def test_ioptions_nested_section(connected_app):
    section = connected_app.service_provider.get_service(
        IOptions["database.users"]
    )
    assert section["connection_string"].startswith("mongodb://")
    assert section["database_name"] == "users_db"


def test_ioptions_rabbit_section(connected_app):
    section = connected_app.service_provider.get_service(IOptions["rabbitmq.tasks"])
    assert section["queue"] == "task_queue"
    assert section["url"].startswith("amqp://")
