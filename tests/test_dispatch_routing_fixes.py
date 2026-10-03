"""Regression tests for dbsource member contexts, request logging, routing and server source."""
import asyncio
from unittest.mock import MagicMock

from bclib.context import (ClientSourceContext, ClientSourceMemberContext,
                           HttpContext, RESTfulContext, ServerSourceContext)
from bclib.context.context_factory import ContextFactory
from bclib.context.merge_type import MergeType
from bclib.listener.http.http_message import HttpMessage

from helpers import cms_content, make_cms, run_dispatch

TWO_MEMBERS = """
<basis core='dbsource' name='demo' source='basiscore'>
  <member name='first' type='list'></member>
  <member name='second' type='list'></member>
</basis>
"""


def _factory(app, logger=None) -> ContextFactory:
    factory = app.service_provider.create_instance(
        ContextFactory, lookup=app._Dispatcher__look_up, logger=logger or MagicMock())
    factory.rebuild_router()
    return factory


def _http_message(full_url: str, url: str, method: str = "get") -> HttpMessage:
    return HttpMessage({"cms": {
        "request": {"full-url": full_url, "url": url, "methode": method},
        "query": {}, "form": {}}})


def _receive(app, message: HttpMessage) -> dict:
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    loop.run_until_complete(app.on_message_receive_async(message))
    return message.response_data


# Bug 1: every member handler gets its own member context

def test_each_member_handler_receives_its_own_member_context(app):
    @app.client_source_handler()
    def source(context: ClientSourceContext):
        return {"rows": 1}

    @app.client_source_member_handler(app.equal("context.member.name", "first"))
    def first(context: ClientSourceMemberContext):
        context.key_field_name = "first_key"
        return {"member": context.member.name}

    @app.client_source_member_handler(app.equal("context.member.name", "second"))
    def second(context: ClientSourceMemberContext):
        context.key_field_name = "second_key"
        context.merge_type = MergeType.APPEND
        return {"member": context.member.name}

    cms = make_cms(form={"command": TWO_MEMBERS, "dmnid": "1"})
    payload = cms_content(run_dispatch(
        app, ClientSourceContext(cms, app, HttpMessage(cms))))

    first_src, second_src = payload["sources"]
    assert first_src["data"] == {"member": "first"}
    assert second_src["data"] == {"member": "second"}
    assert first_src["options"]["tableName"] == "demo.first"
    assert first_src["options"]["keyFieldName"] == "first_key"
    assert first_src["options"]["mergeType"] == MergeType.REPLACE.value
    assert second_src["options"]["tableName"] == "demo.second"
    assert second_src["options"]["keyFieldName"] == "second_key"
    assert second_src["options"]["mergeType"] == MergeType.APPEND.value


# Bug 2: the request log shows the CMS method ('methode')

def test_request_log_shows_cms_methode(app):
    @app.restful_handler("hello")
    def hello(context: RESTfulContext):
        return {"ok": True}

    logger = MagicMock()
    _factory(app, logger).create_context(
        _http_message("localhost/hello", "hello", method="post"))

    log_line = logger.info.call_args[0][0]
    assert log_line.endswith(" post localhost/hello")


# Bug 3: routes match whole path segments of the request path

def _shadowing_app(app):
    @app.restful_handler("users")
    def users(context: RESTfulContext):
        return {"route": "users"}

    @app.web_handler("users/profile")
    def profile(context: HttpContext):
        return "profile"
    return app


def test_shorter_route_does_not_shadow_longer_route_of_other_type(app):
    factory = _factory(_shadowing_app(app))

    assert type(factory.create_context(
        _http_message("localhost/users/profile", "users/profile"))) is HttpContext
    assert type(factory.create_context(
        _http_message("localhost/users", "users"))) is RESTfulContext


def test_shadowed_route_is_dispatched_to_its_handler(app):
    app = _shadowing_app(app)
    app._Dispatcher__context_factory = _factory(app)

    response = _receive(app, _http_message("localhost/users/profile", "users/profile"))

    assert response["cms"]["content"] == "profile"


def test_route_matching_ignores_host_port_and_query(app):
    @app.web_handler("page")
    def page(context: HttpContext):
        return "page"

    @app.restful_handler("users/:id")
    def user(context: RESTfulContext):
        return {"id": context.url_segments["id"]}

    factory = _factory(app)
    route = factory.create_context

    assert type(route(_http_message("example.com:8080/users/42?page=users", "users/42"))) is RESTfulContext
    # host and query text must not be taken for the path
    assert type(route(_http_message("users:8080/page?x=users/1", "page"))) is HttpContext
    # a param route matches exactly one segment
    assert type(route(_http_message("localhost/users/42/extra", "users/42/extra"))) is not RESTfulContext
    # a route must start at the beginning of the path
    assert type(route(_http_message("localhost/admin/users/42", "admin/users/42"))) is not RESTfulContext


def test_wildcard_and_message_type_fallback_are_preserved(app):
    @app.restful_handler("api/:*rest")
    def api(context: RESTfulContext):
        return {}

    factory = _factory(app)
    assert type(factory.create_context(
        _http_message("localhost/api/a/b/c", "api/a/b/c"))) is RESTfulContext
    # no route matches -> fall back by message type
    assert type(factory.create_context(
        _http_message("localhost/other", "other"))) is HttpContext

    @app.restful_handler()
    def any_rest(context: RESTfulContext):
        return {}

    factory = _factory(app)
    # a handler without a route still catches every unmatched path
    assert type(factory.create_context(
        _http_message("localhost/other", "other"))) is RESTfulContext


# Bug 4: a server source routed from HTTP gives a clear 400 instead of KeyError 500

def test_server_source_over_http_returns_bad_request(app):
    @app.server_source_handler()
    def source(context: ServerSourceContext):
        return []

    app._Dispatcher__context_factory = _factory(app)
    response = _receive(app, _http_message("localhost/data", "data"))

    assert response["cms"]["webserver"]["headercode"].startswith("400")
    assert "command" in response["cms"]["content"]
    assert "KeyError" not in response["cms"]["content"]


# Scoped context descriptors must not accumulate per request (memory leak)

def _descriptor_count(app, service_type) -> int:
    return len(app.service_provider._descriptors.get(service_type, []))


def test_context_descriptors_do_not_grow_per_request(app):
    @app.restful_handler("hello")
    def hello(context: RESTfulContext):
        return {"ok": True}

    @app.client_source_handler()
    def source(context: ClientSourceContext):
        return {"rows": 1}

    @app.client_source_member_handler()
    def member(context: ClientSourceMemberContext):
        return {"member": context.member.name}

    for _ in range(50):
        cms = make_cms(url="hello")
        run_dispatch(app, RESTfulContext(cms, app, HttpMessage(cms)))
    for _ in range(5):
        cms = make_cms(form={"command": TWO_MEMBERS, "dmnid": "1"})
        run_dispatch(app, ClientSourceContext(cms, app, HttpMessage(cms)))

    assert _descriptor_count(app, RESTfulContext) == 1
    assert _descriptor_count(app, ClientSourceContext) == 1
    assert _descriptor_count(app, ClientSourceMemberContext) == 1


def test_back_to_back_scopes_resolve_their_own_context(app):
    cms_a, cms_b = make_cms(url="a"), make_cms(url="b")
    context_a = RESTfulContext(cms_a, app, HttpMessage(cms_a))
    context_b = RESTfulContext(cms_b, app, HttpMessage(cms_b))

    assert context_a.services.get_service(RESTfulContext) is context_a
    assert context_b.services.get_service(RESTfulContext) is context_b
    assert _descriptor_count(app, RESTfulContext) == 1
