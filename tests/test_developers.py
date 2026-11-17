import pytest

from tests.conftest import FRONTEND_ID, new_developer


def developers(client, **params) -> list[dict]:
    r = client.get("/getDevelopers", params=params)
    assert r.status_code == 200
    return r.json()


def by_id(client, dev_id: str) -> dict:
    return next(d for d in developers(client) if d["id"] == dev_id)


def test_list_matches_seed_shape(client):
    devs = developers(client)
    assert len(devs) == 17
    assert list(devs[0]) == ["id", "name", "email", "job", "age", "salary", "image", "skills"]


def test_filter_by_job_and_skill(client):
    frontend = developers(client, job="frontend developer")
    assert frontend and all(d["job"] == "Frontend Developer" for d in frontend)
    html = developers(client, skill="html")
    assert html and all("HTML" in d["skills"] for d in html)


def test_exercise_4_1_queries(client):
    """The data supports every query in exercise 4.1."""
    devs = developers(client)
    assert sum("HTML" in d["skills"] for d in devs) > 0
    assert any(30 <= d["age"] <= 50 for d in devs)
    assert any("alphatech" in d["email"].lower() for d in devs)
    assert any(d["age"] <= 30 for d in devs)


def test_create(client):
    r = client.post("/createDeveloper", json=new_developer())
    assert r.status_code == 201
    assert r.json() == {
        "status": "success",
        "message": "Developer data received and saved successfully.",
    }
    assert by_id(client, "test-dev-1")["name"] == "John Doe"


def test_create_without_id_gets_one(client):
    body = new_developer()
    del body["id"]
    assert client.post("/createDeveloper", json=body).status_code == 201
    created = [d for d in developers(client) if d["email"] == "john@doe.com"]
    assert len(created) == 1 and created[0]["id"]


def test_create_duplicate_id(client):
    r = client.post("/createDeveloper", json=new_developer(id=FRONTEND_ID))
    assert r.status_code == 409
    assert r.json()["status"] == "error"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "not-an-email"),
        ("age", 5),
        ("salary", -1),
        ("name", "   "),
        ("image", "not a url"),
        ("skills", [""]),
    ],
)
def test_create_validation(client, field, value):
    r = client.post("/createDeveloper", json=new_developer(**{field: value}))
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"][-1] in (field, 0)


def test_create_dedupes_skills(client):
    client.post("/createDeveloper", json=new_developer(skills=["HTML", "CSS", "HTML"]))
    assert by_id(client, "test-dev-1")["skills"] == ["HTML", "CSS"]


def test_partial_update_keeps_other_fields(client):
    before = by_id(client, FRONTEND_ID)
    r = client.put("/updateDeveloper", json={"id": FRONTEND_ID, "salary": 2575000})
    assert r.status_code == 200
    assert r.json()["message"] == "Developer data updated successfully."
    after = by_id(client, FRONTEND_ID)
    assert after == before | {"salary": 2575000}


def test_full_update(client):
    body = by_id(client, FRONTEND_ID) | {"age": 24, "skills": ["HTML"]}
    assert client.put("/updateDeveloper", json=body).status_code == 200
    assert by_id(client, FRONTEND_ID) == body


def test_update_unknown(client):
    r = client.put("/updateDeveloper", json={"id": "nope", "salary": 1})
    assert r.status_code == 404
    assert r.json() == {"status": "error", "message": "Developer not found."}


def test_update_needs_a_change(client):
    r = client.put("/updateDeveloper", json={"id": FRONTEND_ID})
    assert r.status_code == 422


def test_update_validates_values(client):
    r = client.put("/updateDeveloper", json={"id": FRONTEND_ID, "email": "broken"})
    assert r.status_code == 422


def test_delete(client):
    r = client.request("DELETE", "/deleteDeveloper", json={"id": FRONTEND_ID})
    assert r.status_code == 200
    assert r.json()["message"] == "Developer data deleted successfully."
    assert len(developers(client)) == 16
    r = client.request("DELETE", "/deleteDeveloper", json={"id": FRONTEND_ID})
    assert r.status_code == 404


def test_exercise_4_2_salary_raise(client):
    """Raise every frontend developer's salary by 3%, as the exercise describes."""
    frontend = [d for d in developers(client) if d["job"] == "Frontend Developer"]
    for d in frontend:
        r = client.put(
            "/updateDeveloper", json={"id": d["id"], "salary": round(d["salary"] * 1.03)}
        )
        assert r.status_code == 200
    for d in frontend:
        assert by_id(client, d["id"])["salary"] == round(d["salary"] * 1.03)


def test_fractional_salary_round_trips(client):
    client.put("/updateDeveloper", json={"id": FRONTEND_ID, "salary": 360500.5})
    assert by_id(client, FRONTEND_ID)["salary"] == 360500.5
