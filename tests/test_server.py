import json
from http.server import ThreadingHTTPServer
from importlib.metadata import version
from threading import Thread
from unittest.mock import MagicMock
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from cicd_demo.server import DemoHandler
from cicd_demo.server import main as server_main


@pytest.fixture(scope="module")
def base_url():
    with ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{server.server_port}"
        server.shutdown()
        thread.join(timeout=5)


def get(base_url, path):
    try:
        response = urlopen(base_url + path, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def test_homepage_is_packaged(base_url):
    status, headers, body = get(base_url, "/")
    assert status == 200
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert int(headers["Content-Length"]) == len(body)
    assert b"This page ships inside the Python wheel." in body


def test_health_reports_installed_version(base_url):
    status, headers, body = get(base_url, "/health")
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert json.loads(body) == {"status": "ok", "version": version("cicd-demo")}


@pytest.mark.parametrize(("subtotal", "fee"), [("0", 500), ("4999", 500), ("5000", 0)])
def test_quote_api(base_url, subtotal, fee):
    status, _, body = get(base_url, f"/api/quote?subtotal_cents={subtotal}")
    assert status == 200
    assert json.loads(body) == {
        "subtotal_cents": int(subtotal),
        "shipping_cents": fee,
        "total_cents": int(subtotal) + fee,
    }


@pytest.mark.parametrize(
    "query",
    [
        "",
        "subtotal_cents=",
        "subtotal_cents=-1",
        "subtotal_cents=1.5",
        "subtotal_cents=abc",
        "subtotal_cents=1&subtotal_cents=2",
        "subtotal_cents=%D9%A1",
        "subtotal_cents=%2B5",
    ],
)
def test_invalid_quote_returns_400(base_url, query):
    status, _, body = get(base_url, f"/api/quote?{query}")
    assert status == 400
    assert "error" in json.loads(body)


def test_unknown_route_returns_404(base_url):
    status, _, body = get(base_url, "/missing")
    assert status == 404
    assert json.loads(body) == {"error": "not found"}


@pytest.mark.parametrize("interrupted", [False, True])
def test_cli_binds_requested_address_and_closes_server(monkeypatch, capsys, interrupted):
    server = MagicMock()
    server.server_port = 12345
    if interrupted:
        server.serve_forever.side_effect = KeyboardInterrupt
    factory = MagicMock()
    factory.return_value.__enter__.return_value = server
    monkeypatch.setattr("cicd_demo.server.ThreadingHTTPServer", factory)
    monkeypatch.setattr("sys.argv", ["cicd-demo", "--host", "127.0.0.1", "--port", "0"])
    server_main()
    factory.assert_called_once_with(("127.0.0.1", 0), DemoHandler)
    assert json.loads(capsys.readouterr().out) == {"host": "127.0.0.1", "port": 12345}
    factory.return_value.__exit__.assert_called_once()
