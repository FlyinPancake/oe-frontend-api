import random
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_rng
from app.main import create_app

FRONTEND_ID = "a49335ca-d76a-02d1-2a6c-fdab1a3f8c0a"  # Linda Hamilton, salary 2 500 000


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(token_ttl_seconds=60))
    app.dependency_overrides[get_rng] = lambda: random.Random(42)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def token(client: TestClient) -> str:
    r = client.post("/login", json={"username": "johndoe", "password": "johndoe123"})
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def new_developer(**overrides) -> dict:
    return {
        "id": "test-dev-1",
        "name": "John Doe",
        "email": "john@doe.com",
        "job": "Fullstack Developer",
        "age": 40,
        "salary": 650000,
        "image": "https://randomuser.me/api/portraits/men/1.jpg",
        "skills": ["Angular", "Node.js", "MongoDB"],
    } | overrides
