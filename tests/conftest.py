"""Shared fixtures for the Edge unit suite."""
import pytest

from bclib import edge
from bclib.dispatcher import IDispatcher


@pytest.fixture
def app() -> IDispatcher:
    return edge.from_options({"name": "pytest-edge", "router": "restful"})


@pytest.fixture
def connected_app() -> IDispatcher:
    return edge.from_options(
        {
            "name": "pytest-connections",
            "router": "restful",
            "database": {
                "users": {
                    "connection_string": "mongodb://localhost:27017",
                    "database_name": "users_db",
                }
            },
            "rabbitmq": {
                "tasks": {
                    "url": "amqp://guest:guest@localhost:5672/",
                    "queue": "task_queue",
                    "durable": True,
                }
            },
            "external_api": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "headers": {"X-Test": "1"},
                "ssl_verify": False,
            },
            "logger": {"level": "WARNING"},
        }
    )
