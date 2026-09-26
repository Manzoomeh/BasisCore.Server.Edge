"""Static file handler coverage."""
from pathlib import Path

import pytest

from bclib.utility.static_file_handler import StaticFileHandler


def test_static_handler_requires_existing_dir(tmp_path: Path):
    with pytest.raises(ValueError):
        StaticFileHandler(str(tmp_path / "missing"))


def test_static_handler_safe_path_and_extensions(tmp_path: Path):
    (tmp_path / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "secret.exe").write_bytes(b"x")

    handler = StaticFileHandler(
        str(tmp_path),
        allowed_extensions={".html", ".js"},
        enable_index=True,
        url_prefix="/static",
    )

    assert handler._is_allowed_extension(tmp_path / "app.js") is True
    assert handler._is_allowed_extension(tmp_path / "secret.exe") is False
    assert handler._is_safe_path(tmp_path / "index.html") is True
    assert handler._is_safe_path(tmp_path / ".." / "etc" / "passwd") is False
    assert handler._normalize_url_path("/static/app.js") == "app.js"
    assert "html" in handler._get_mime_type(tmp_path / "index.html")


def test_add_static_handler_on_dispatcher(app, tmp_path: Path):
    (tmp_path / "index.html").write_text("x", encoding="utf-8")
    handler = StaticFileHandler(str(tmp_path))
    app.add_static_handler(handler)
