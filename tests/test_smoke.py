"""Smoke checks for public package surface used by consumers."""
import ast
from pathlib import Path


def test_package_version():
    import bclib

    assert bclib.__version__ == "4.1.0"


def test_edge_import():
    from bclib import edge

    assert callable(edge.from_options)
    assert callable(edge.from_config)


def test_di_public_exports():
    from bclib.di import (
        InjectionPlan,
        InjectionStrategy,
        ServiceDescriptor,
        ServiceLifetime,
        ServiceProvider,
        ServiceStrategy,
        ValueStrategy,
        create_service_container,
    )

    assert ServiceProvider.__module__ == "bclib.di.service_provider"
    assert ServiceLifetime.SINGLETON.value == "singleton"
    assert callable(create_service_container)
    assert InjectionPlan is not None
    assert issubclass(ServiceStrategy, ValueStrategy)
    assert issubclass(ValueStrategy, InjectionStrategy)
    assert ServiceDescriptor is not None


def test_rabbit_message_module_has_no_pika_import():
    """aio-pika path must not hard-require pika at RabbitMessage import time."""
    source = Path("bclib/listener/rabbit/rabbit_message.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert not any("pika" in name for name in imported)
