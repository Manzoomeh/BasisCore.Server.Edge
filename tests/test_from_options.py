"""Lightweight from_options smoke (no listening / no network bind)."""
from bclib import edge
from bclib.dispatcher import IDispatcher


def test_from_options_returns_dispatcher():
    app = edge.from_options(
        {
            "name": "pytest-smoke",
            "router": "restful",
        }
    )

    assert isinstance(app, IDispatcher)
