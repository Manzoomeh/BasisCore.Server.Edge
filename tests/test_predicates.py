"""Predicate helper coverage."""
import asyncio

from bclib.context import RESTfulContext

from helpers import http_context, make_cms


def test_url_predicate_matches_and_fills_segments(app):
    cms = make_cms(url="api/users/7", method="get")
    ctx = http_context(app, cms, RESTfulContext)
    pred = app.url("api/users/:id")

    assert asyncio.run(pred.check_async(ctx)) is True
    assert ctx.url_segments["id"] == "7"


def test_url_predicate_rejects_mismatch(app):
    cms = make_cms(url="api/other", method="get")
    ctx = http_context(app, cms, RESTfulContext)

    assert asyncio.run(app.url("api/users/:id").check_async(ctx)) is False


def test_method_predicates(app):
    get_ctx = http_context(app, make_cms(method="get"), RESTfulContext)
    post_ctx = http_context(app, make_cms(method="post"), RESTfulContext)

    assert asyncio.run(app.is_get().check_async(get_ctx)) is True
    assert asyncio.run(app.is_post().check_async(get_ctx)) is False
    assert asyncio.run(app.is_post().check_async(post_ctx)) is True


def test_combined_get_url_predicate(app):
    cms = make_cms(url="items/1", method="get")
    ctx = http_context(app, cms, RESTfulContext)

    assert asyncio.run(app.get("items/:id").check_async(ctx)) is True
    assert ctx.url_segments["id"] == "1"


def test_has_value_and_equal(app):
    cms = make_cms(query={"q": "abc"})
    ctx = http_context(app, cms, RESTfulContext)

    assert asyncio.run(app.has_value("context.query.q").check_async(ctx)) is True
    assert asyncio.run(app.equal("context.query.q", "abc").check_async(ctx)) is True
    assert asyncio.run(app.equal("context.query.q", "xyz").check_async(ctx)) is False


def test_all_and_any_combinators(app):
    cms = make_cms(url="x", method="get")
    ctx = http_context(app, cms, RESTfulContext)

    assert asyncio.run(app.all(app.is_get(), app.url("x")).check_async(ctx)) is True
    assert asyncio.run(app.any(app.is_post(), app.url("x")).check_async(ctx)) is True
    assert asyncio.run(app.all(app.is_post(), app.url("x")).check_async(ctx)) is False
