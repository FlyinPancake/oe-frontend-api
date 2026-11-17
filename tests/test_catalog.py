import pytest

SEED_SIZE = {"skill": 77, "job": 22}


@pytest.fixture(params=["skill", "job"])
def kind(request) -> str:
    return request.param


def label(kind: str) -> str:
    return kind.capitalize()


def test_list(client, kind):
    items = client.get(f"/{kind}").json()
    assert len(items) == SEED_SIZE[kind]
    assert set(items[0]) == {"id", "name", "description"}


def test_get_one(client, kind):
    first = client.get(f"/{kind}").json()[0]
    assert client.get(f"/{kind}/{first['id']}").json() == first
    r = client.get(f"/{kind}/nope")
    assert r.status_code == 404
    assert r.json() == {"status": f"No {kind} with such ID."}


def test_create(client, kind):
    r = client.post(f"/{kind}", json={"name": "Frontend development", "description": "Lorem"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == f"{label(kind)} created successfully."
    created = body[kind]
    assert created["id"] and created["name"] == "Frontend development"
    assert client.get(f"/{kind}/{created['id']}").json() == created


def test_create_rejects_client_id(client, kind):
    r = client.post(f"/{kind}", json={"name": "X", "id": "client-chosen"})
    assert r.status_code == 422  # the server generates skill and job ids


def test_create_requires_name(client, kind):
    assert client.post(f"/{kind}", json={"description": "no name"}).status_code == 422


def test_update(client, kind):
    first = client.get(f"/{kind}").json()[0]
    changed = first | {"name": "Renamed", "description": "New"}
    r = client.put(f"/{kind}", json=changed)
    assert r.status_code == 200
    assert r.json() == {"status": f"{label(kind)} updated successfully."}
    assert client.get(f"/{kind}/{first['id']}").json() == changed


def test_update_unknown(client, kind):
    r = client.put(f"/{kind}", json={"id": "nope", "name": "X", "description": ""})
    assert r.status_code == 404
    assert r.json() == {"status": f"No {kind} with such ID."}


def test_delete_without_token(client, kind):
    first = client.get(f"/{kind}").json()[0]
    r = client.request("DELETE", f"/{kind}", json={"id": first["id"]})
    assert r.status_code == 401
    assert r.json() == {"status": "Authorization token required."}
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_delete_with_bad_token(client, kind):
    first = client.get(f"/{kind}").json()[0]
    r = client.request(
        "DELETE", f"/{kind}", json={"id": first["id"]}, headers={"Authorization": "Bearer bogus"}
    )
    assert r.status_code == 401
    assert r.json() == {"status": "Invalid or expired token."}


def test_delete_with_token(client, kind, auth):
    first = client.get(f"/{kind}").json()[0]
    r = client.request("DELETE", f"/{kind}", json={"id": first["id"]}, headers=auth)
    assert r.status_code == 200
    assert r.json() == {"status": f"{label(kind)} deleted successfully."}
    assert len(client.get(f"/{kind}").json()) == SEED_SIZE[kind] - 1

    r = client.request("DELETE", f"/{kind}", json={"id": first["id"]}, headers=auth)
    assert r.status_code == 404


def test_skills_cover_exercise_5_2_categories(client):
    """Every seeded skill falls into one of the three categories in exercise 5.2."""
    from tests.skill_categories import CATEGORIES

    known = set().union(*CATEGORIES.values())
    names = {s["name"] for s in client.get("/skill").json()}
    assert names - known == set()
