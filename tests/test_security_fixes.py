"""Escaping of HTML error pages and the static file method check."""
import asyncio
from pathlib import Path

from bclib import edge
from bclib.context import HttpContext
from bclib.listener.http.http_message import HttpMessage
from bclib.utility.static_file_handler import StaticFileHandler


def _send(app, cms: dict) -> dict:
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)

    async def run():
        await app.initialize_task_async()
        message = HttpMessage(cms)
        await app.on_message_receive_async(message)
        return message.response_data["cms"]

    return loop.run_until_complete(run())


def _request(url: str, method: str = "get") -> dict:
    return {"cms": {"request": {"full-url": f"localhost/{url}", "url": url, "methode": method}}}


def test_html_error_page_escapes_the_exception_message():
    app = edge.from_options({"name": "pytest-escape", "log_request": False})

    @app.web_handler("page")
    def page(context: HttpContext):
        raise ValueError("<script>alert(1)</script>")

    reply = _send(app, _request("page"))

    assert reply["webserver"]["headercode"].startswith("500")
    assert "<script>" not in reply["content"]
    assert "&lt;script&gt;" in reply["content"]


def test_html_error_page_escapes_the_traceback():
    app = edge.from_options({"name": "pytest-escape-tb", "log_request": False, "error_log": True})

    @app.web_handler("page")
    def page(context: HttpContext):
        raise ValueError("<img src=x onerror=alert(1)>")

    content = _send(app, _request("page"))["content"]

    assert "<img" not in content
    assert "<hr/>" in content


def test_static_files_are_not_served_for_post(tmp_path: Path):
    (tmp_path / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
    app = edge.from_options({"name": "pytest-static", "log_request": False})
    app.add_static_handler(StaticFileHandler(str(tmp_path), allowed_extensions={".html"}))

    get_reply = _send(app, _request("index.html", "get"))
    post_reply = _send(app, _request("index.html", "post"))

    assert "blob-content" in get_reply
    assert "blob-content" not in post_reply
    assert post_reply["webserver"]["headercode"].startswith("404")
