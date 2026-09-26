"""Cache factory and in-memory cache manager."""
from bclib.cache.cache_status import CacheStatus
from bclib.cache.factory import CacheFactory
from bclib.cache.in_memory_cache_manager import InMemoryCacheManager
from bclib.cache.no_cache import NoCacheManager
from bclib.utility import DictEx


def test_cache_factory_defaults_to_no_cache():
    assert isinstance(CacheFactory.create(None), NoCacheManager)


def test_cache_factory_memory():
    manager = CacheFactory.create(DictEx({"type": "memory"}))
    assert isinstance(manager, InMemoryCacheManager)


def test_cache_factory_unknown_type():
    import pytest

    with pytest.raises(ValueError):
        CacheFactory.create(DictEx({"type": "redis"}))


def test_in_memory_add_get_reset():
    manager = InMemoryCacheManager(DictEx({"type": "memory"}))
    status = manager.add_or_update("k1", {"v": 1}, life_time=0)
    assert status in (CacheStatus.ADDED, CacheStatus.UPDATED)
    assert manager.get_cache("k1") == {"v": 1}
    assert manager.reset(["k1"]) == CacheStatus.RESET


def test_dispatcher_cache_from_options():
    from bclib import edge

    app = edge.from_options(
        {
            "name": "cache-app",
            "router": "restful",
            "cache": {"type": "memory"},
        }
    )
    assert isinstance(app.cache_manager, InMemoryCacheManager)
