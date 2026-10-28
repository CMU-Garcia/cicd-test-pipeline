import json
from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from cicd_demo.server import app, get_app_version
from cicd_demo.server import main as server_main

client = TestClient(app)


def test_homepage_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "This page ships inside the Python wheel." in response.text


def test_homepage_fallback_when_resource_missing():
    with patch("cicd_demo.server.files", side_effect=Exception("Missing")):
        response = client.get("/")
        assert response.status_code == 200
        assert "CI/CD FastAPI Demo" in response.text


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_get_app_version_fallback():
    with patch("cicd_demo.server.version", side_effect=PackageNotFoundError):
        assert get_app_version() == "0.1.0"


@pytest.mark.parametrize(
    ("subtotal", "shipping", "total"),
    [
        ("0", 500, 500),
        ("4999", 500, 5499),
        ("5000", 0, 5000),
    ],
)
def test_quote_endpoint(subtotal, shipping, total):
    response = client.get(f"/api/quote?subtotal_cents={subtotal}")
    assert response.status_code == 200
    assert response.json() == {
        "subtotal_cents": int(subtotal),
        "shipping_cents": shipping,
        "total_cents": total,
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
def test_invalid_quote_returns_400(query):
    response = client.get(f"/api/quote?{query}")
    assert response.status_code == 400
    assert "error" in response.json()


def test_unknown_route_returns_404():
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.json() == {"error": "not found"}


def test_openapi_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200


@pytest.mark.parametrize("interrupted", [False, True])
def test_cli_binds_requested_address_and_closes_server(monkeypatch, capsys, interrupted):
    mock_run = MagicMock()
    if interrupted:
        mock_run.side_effect = KeyboardInterrupt
    monkeypatch.setattr("uvicorn.run", mock_run)
    monkeypatch.setattr("sys.argv", ["cicd-demo", "--host", "127.0.0.1", "--port", "0"])

    try:
        server_main()
    except KeyboardInterrupt:
        pass

    mock_run.assert_called_once()
    output = json.loads(capsys.readouterr().out)
    assert output["host"] == "127.0.0.1"
    assert isinstance(output["port"], int)
    assert output["port"] > 0
