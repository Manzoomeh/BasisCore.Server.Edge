"""Process lifecycle: HTTP listener shutdown, signal ownership, launcher and streaming."""
import asyncio
import signal
import socket
import sys
from unittest.mock import patch

import aiohttp
import pytest

from bclib import edge
from bclib.context import RESTfulContext
from bclib.di import IHostedService


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _is_listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


async def _wait_for_bind_async(port: int) -> None:
    for _ in range(50):
        if _is_listening(port):
            return
        await asyncio.sleep(0.1)
    raise AssertionError(f"listener did not bind port {port}")


def _http_app(port: int, name: str = "pytest-http"):
    return edge.from_options(
        {"name": name, "router": "restful", "http": f"127.0.0.1:{port}"})


def _cancel_pending(loop: asyncio.AbstractEventLoop) -> list:
    pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
    for task in pending:
        task.cancel()
    return loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


@pytest.fixture
def http_app():
    port = _free_port()
    app = _http_app(port)
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    yield app, loop, port
    if not loop.is_closed():
        _cancel_pending(loop)


def _self_signed_cert(directory) -> dict:
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
            .sign(key, hashes.SHA256()))
    certfile, keyfile = directory / "cert.pem", directory / "key.pem"
    certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    keyfile.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    return {"certfile": str(certfile), "keyfile": str(keyfile)}


# --- HTTP listener shutdown (ssl attribute, cleanup) ---------------------------

@pytest.mark.parametrize("use_ssl", [False, True], ids=["http", "https"])
def test_cancelling_http_listener_stops_server_without_error(use_ssl, tmp_path):
    port = _free_port()
    http = {"endpoint": f"127.0.0.1:{port}"}
    if use_ssl:
        http["ssl"] = _self_signed_cert(tmp_path)
    app = edge.from_options({"name": "pytest-http", "router": "restful", "http": http})
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    loop.run_until_complete(app.initialize_task_async())
    loop.run_until_complete(_wait_for_bind_async(port))

    results = _cancel_pending(loop)

    errors = [r for r in results if isinstance(r, Exception)
              and not isinstance(r, asyncio.CancelledError)]
    assert errors == []
    assert not _is_listening(port)


def test_http_listener_does_not_install_aiohttp_signal_handlers(http_app):
    from aiohttp import web
    app, loop, port = http_app
    seen = []
    original = web.AppRunner.__init__

    def spy(self, *args, **kwargs):
        seen.append(kwargs.get("handle_signals", False))
        original(self, *args, **kwargs)

    with patch.object(web.AppRunner, "__init__", spy):
        loop.run_until_complete(app.initialize_task_async())
        loop.run_until_complete(_wait_for_bind_async(port))

    assert seen == [False]


class _RecordingService(IHostedService):
    events: list = []

    async def start_async(self) -> None:
        _RecordingService.events.append("start")

    async def stop_async(self) -> None:
        _RecordingService.events.append("stop")


def test_signal_runs_graceful_shutdown_and_releases_http_port():
    """SIGINT handled by the dispatcher: hosted services stop, HTTP port is released."""
    port = _free_port()
    app = _http_app(port, "pytest-signal")
    app.service_provider.add_singleton(
        IHostedService, _RecordingService, is_hosted=True)
    _RecordingService.events = []
    loop = app.service_provider.get_service(asyncio.AbstractEventLoop)
    observed = {}

    async def send_signal_when_bound():
        await _wait_for_bind_async(port)
        observed["listening"] = True
        signal.raise_signal(signal.SIGINT)

    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        loop.call_soon(lambda: loop.create_task(send_signal_when_bound()))
        app.listening()
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)

    assert observed.get("listening")
    assert _RecordingService.events == ["start", "stop"]
    assert not _is_listening(port)


# --- from_list without a current event loop (Python 3.14 behaviour) ------------

def test_from_list_runs_when_no_current_event_loop():
    def no_loop():
        raise RuntimeError("There is no current event loop in thread 'MainThread'.")

    with patch("subprocess.run") as run_mock, patch("bclib.edge.__print_splash"), \
            patch("asyncio.get_event_loop", no_loop):
        run_mock.return_value = 0
        edge.from_list({"api": ["python", "api_app.py"]})

    assert run_mock.call_count == 1


# --- command line options --------------------------------------------------------

@pytest.mark.parametrize("argv", [["--Name", "from-long"], ["--Name=from-long"], ["-n", "from-long"]])
def test_name_option_sets_application_name(argv):
    options = {"name": "default", "router": "restful"}
    with patch.object(sys, "argv", ["app.py", *argv]):
        edge.from_options(options)
    assert options["name"] == "from-long"


def test_multi_option_suppresses_splash():
    with patch.object(sys, "argv", ["app.py", "--Multi"]), \
            patch("bclib.edge.__print_splash") as splash:
        edge.from_options({"router": "restful"})
    splash.assert_not_called()


# --- HTTP streaming through the real listener -------------------------------------

def test_streaming_response_through_http_listener(http_app):
    app, loop, port = http_app

    @app.restful_handler(app.url("stream"))
    async def stream(context: RESTfulContext):
        await context.start_stream_response_async(
            status=200, headers={"Content-Type": "text/plain"})
        for chunk in (b"one,", b"two,", b"three"):
            await context.write_and_drain_async(chunk)

    async def fetch():
        await _wait_for_bind_async(port)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:{port}/stream") as response:
                return response.status, await response.read()

    loop.run_until_complete(app.initialize_task_async())
    status, body = loop.run_until_complete(asyncio.wait_for(fetch(), 10))

    assert status == 200
    assert body == b"one,two,three"
