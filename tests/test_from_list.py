"""from_list multi-host launcher (subprocess mocked)."""
from unittest.mock import patch

from bclib import edge


def test_from_list_runs_subprocess_for_each_host():
    hosts = {
        "api": ["python", "api_app.py"],
        "web": ["python", "web_app.py"],
    }

    with patch("subprocess.run") as run_mock, patch("bclib.edge.__print_splash"):
        # from_list uses ThreadPoolExecutor + asyncio gather; keep run fast
        run_mock.return_value = 0
        edge.from_list(hosts)

    assert run_mock.call_count == 2
    # Extra args -n and -m are appended
    called_args = [call.args[0] for call in run_mock.call_args_list]
    assert any("-m" in args for args in called_args)
