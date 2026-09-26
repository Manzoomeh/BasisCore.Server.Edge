"""Listener factory, endpoint parsing, and SSL/PFX helpers."""
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509.oid import NameOID

from bclib import edge
from bclib.listener import IListenerFactory
from bclib.listener.endpoint import Endpoint
from bclib.listener.http.http_listener import HttpListener
from bclib.listener.rabbit.rabbit_listener import RabbitListener
from bclib.listener.tcp.tcp_listener import TcpListener


def test_endpoint_parses_host_port():
    ep = Endpoint("127.0.0.1:9090")
    assert ep.host == "127.0.0.1"
    assert ep.port == 9090


def test_endpoint_default_port():
    ep = Endpoint("localhost")
    assert ep.host == "localhost"
    assert ep.port == 80


def test_listener_factory_empty_when_no_endpoints(app):
    factory = app.service_provider.get_service(IListenerFactory)
    assert factory.load_listeners() == []


def test_listener_factory_creates_instances_without_binding():
    app = edge.from_options(
        {
            "name": "listeners",
            "router": "restful",
            "http": "127.0.0.1:18080",
            "tcp": "127.0.0.1:13000",
            "rabbitmq": {
                "url": "amqp://guest:guest@localhost:5672/",
                "queue": "edge-tests",
            },
        }
    )
    factory = app.service_provider.get_service(IListenerFactory)
    listeners = factory.load_listeners()
    types = {type(listener) for listener in listeners}
    assert HttpListener in types
    assert TcpListener in types
    assert RabbitListener in types
    # Must not call initialize_task / listening in unit tests


def test_http_listener_keeps_ssl_options():
    app = edge.from_options(
        {
            "name": "ssl-opts",
            "router": "restful",
            "http": {
                "endpoint": "0.0.0.0:443",
                "ssl": {"certfile": "cert.pem", "keyfile": "key.pem"},
            },
        }
    )
    listeners = app.service_provider.get_service(IListenerFactory).load_listeners()
    http = next(listener for listener in listeners if isinstance(listener, HttpListener))
    options = object.__getattribute__(http, "_HttpListener__options")
    assert options.get("ssl")["certfile"] == "cert.pem"


def test_convert_pfx_to_temp_files(tmp_path: Path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "edge-test")]
    )
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    pfx_path = tmp_path / "test.pfx"
    pfx_bytes = pkcs12.serialize_key_and_certificates(
        name=b"edge",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(b"secret"),
    )
    pfx_path.write_bytes(pfx_bytes)

    fullchain, key_file = HttpListener.convert_pfx_to_temp_files(
        str(pfx_path), "secret"
    )
    try:
        assert Path(fullchain).exists()
        assert Path(key_file).exists()
        assert b"BEGIN CERTIFICATE" in Path(fullchain).read_bytes()
        assert b"BEGIN" in Path(key_file).read_bytes()
    finally:
        Path(fullchain).unlink(missing_ok=True)
        Path(key_file).unlink(missing_ok=True)
