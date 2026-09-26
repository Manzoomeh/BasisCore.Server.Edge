"""Focused unit tests for the public DI API."""
from bclib.di import ServiceLifetime, ServiceProvider, create_service_container


class IGreeter:
    def greet(self) -> str:
        raise NotImplementedError


class Greeter(IGreeter):
    def greet(self) -> str:
        return "hello"


class Counter:
    def __init__(self) -> None:
        self.value = 0

    def bump(self) -> int:
        self.value += 1
        return self.value


def test_singleton_resolves_same_instance():
    services = ServiceProvider()
    services.add_singleton(IGreeter, Greeter)

    first = services.get_service(IGreeter)
    second = services.get_service(IGreeter)

    assert isinstance(first, Greeter)
    assert first is second
    assert first.greet() == "hello"
    assert services.get_lifetime(IGreeter) == ServiceLifetime.SINGLETON


def test_transient_resolves_new_instance():
    services = ServiceProvider()
    services.add_transient(Counter, Counter)

    first = services.get_service(Counter)
    second = services.get_service(Counter)

    assert first is not second
    assert services.get_lifetime(Counter) == ServiceLifetime.TRANSIENT


def test_scoped_instances_differ_across_sibling_scopes():
    services = ServiceProvider()
    services.add_scoped(Counter, Counter)

    scope_a = services.create_scope()
    scope_b = services.create_scope()

    first = scope_a.get_service(Counter)
    second = scope_b.get_service(Counter)

    assert first is not second
    assert scope_a.get_service(Counter) is first
    assert services.get_lifetime(Counter) == ServiceLifetime.SCOPED


def test_scoped_child_reuses_parent_instance_when_already_resolved():
    """Scoped resolution walks the parent chain (request-style nesting)."""
    services = ServiceProvider()
    services.add_scoped(Counter, Counter)

    parent_instance = services.get_service(Counter)
    child = services.create_scope()

    assert child.get_service(Counter) is parent_instance


def test_multiple_implementations_as_list():
    class IListener:
        pass

    class HttpListener(IListener):
        pass

    class TcpListener(IListener):
        pass

    services = ServiceProvider()
    services.add_singleton(IListener, HttpListener)
    services.add_singleton(IListener, TcpListener)

    first = services.get_service(IListener)
    all_listeners = services.get_service(list[IListener])

    assert isinstance(first, HttpListener)
    assert len(all_listeners) == 2
    assert isinstance(all_listeners[0], HttpListener)
    assert isinstance(all_listeners[1], TcpListener)


def test_create_service_container_registers_provider():
    container = create_service_container()
    provider = container.get_service(ServiceProvider)

    assert provider is container
