import pytest
from pydantic import ValidationError

from app.config import Settings
from app.dependencies import TokenRegistry
from app.main import create_app
from app.models import DeveloperUpdate
from tests.conftest import FRONTEND_ID


def test_login_wrong_password(client):
    r = client.post("/login", json={"username": "johndoe", "password": "nope"})
    assert r.status_code == 401
    assert r.json() == {"error": "Invalid username or password."}


def test_login_returns_hex_token(token):
    assert len(token) == 64
    int(token, 16)


def test_credentials_come_from_settings(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("API_DEMO_USERNAME", "teacher")
    monkeypatch.setenv("API_DEMO_PASSWORD", "s3cret")
    with TestClient(create_app(Settings())) as c:
        assert (
            c.post("/login", json={"username": "teacher", "password": "s3cret"}).status_code == 200
        )
        assert (
            c.post("/login", json={"username": "johndoe", "password": "johndoe123"}).status_code
            == 401
        )


def test_token_expiry(monkeypatch):
    now = 1000.0
    monkeypatch.setattr("app.dependencies.time.monotonic", lambda: now)
    tokens = TokenRegistry(ttl_seconds=10)
    tokens.add("t")
    assert tokens.is_valid("t")
    now = 1011.0
    assert not tokens.is_valid("t")
    assert not tokens.is_valid("unknown")


def test_status(client):
    r = client.get("/status", headers={"X-Request-ID": "abc123"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "status", "meta", "health", "performance", "demo"}
    assert body["status"] == "ok"
    assert body["meta"]["request_id"] == "abc123"
    assert r.headers["X-Request-ID"] == "abc123"
    assert r.headers["X-Process-Time"].endswith("ms")


def test_request_id_generated(client):
    assert len(client.get("/word").headers["X-Request-ID"]) == 16


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_reset_restores_seed(client, auth, method):
    client.request("DELETE", "/deleteDeveloper", json={"id": FRONTEND_ID})
    client.post("/skill", json={"name": "COBOL"})
    first_job = client.get("/job").json()[0]["id"]
    client.request("DELETE", "/job", json={"id": first_job}, headers=auth)

    r = client.request(method, "/reset")
    assert r.status_code == 200
    assert r.json() | {"message": ""} == {
        "status": "success",
        "message": "",
        "developers": 17,
        "skills": 77,
        "jobs": 22,
        "words": 100,
    }
    assert any(d["id"] == FRONTEND_ID for d in client.get("/getDevelopers").json())
    assert client.get(f"/job/{first_job}").status_code == 200
    # The login survives a data reset.
    assert client.request("DELETE", "/job", json={"id": first_job}, headers=auth).status_code == 200


def test_cors_preflight(client):
    r = client.options(
        "/updateDeveloper",
        headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": "PUT"},
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"


def test_gzip_for_large_responses(client):
    r = client.get("/skill", headers={"Accept-Encoding": "gzip"})
    assert r.headers["content-encoding"] == "gzip"


def test_openapi_lists_every_route(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/word",
        "/getDevelopers",
        "/createDeveloper",
        "/updateDeveloper",
        "/deleteDeveloper",
        "/skill",
        "/skill/{item_id}",
        "/job",
        "/job/{item_id}",
        "/login",
        "/status",
        "/reset",
    } <= set(paths)
    assert "HTTPBearer" in client.get("/openapi.json").json()["components"]["securitySchemes"]


def test_developer_update_model_rejects_id_only():
    with pytest.raises(ValidationError, match="at least one field"):
        DeveloperUpdate(id="x")
