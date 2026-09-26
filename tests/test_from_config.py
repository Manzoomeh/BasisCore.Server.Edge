"""Unit tests for edge.from_config path resolution."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bclib import edge


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    payload = {"name": "unit-test", "router": "restful"}
    (tmp_path / "host.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    (tmp_path / "production.json").write_text(
        json.dumps({**payload, "name": "production"}),
        encoding="utf-8",
    )
    return tmp_path


def test_from_config_loads_host_json_from_directory(config_dir: Path):
    sentinel = MagicMock(name="dispatcher")

    with patch.object(edge, "from_options", return_value=sentinel) as mocked:
        result = edge.from_config(str(config_dir))

    assert result is sentinel
    mocked.assert_called_once()
    options = mocked.call_args.args[0]
    assert options["name"] == "unit-test"
    assert options["router"] == "restful"


def test_from_config_custom_filename(config_dir: Path):
    sentinel = MagicMock(name="dispatcher")

    with patch.object(edge, "from_options", return_value=sentinel) as mocked:
        edge.from_config(str(config_dir), "production.json")

    options = mocked.call_args.args[0]
    assert options["name"] == "production"


def test_from_config_accepts_explicit_json_file(config_dir: Path):
    sentinel = MagicMock(name="dispatcher")
    file_path = config_dir / "host.json"

    with patch.object(edge, "from_options", return_value=sentinel) as mocked:
        edge.from_config(str(file_path))

    mocked.assert_called_once()
    assert mocked.call_args.args[0]["name"] == "unit-test"


def test_from_config_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        edge.from_config(str(tmp_path / "missing-dir"))
