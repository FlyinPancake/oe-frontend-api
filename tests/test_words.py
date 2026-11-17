import pytest


def test_all_words(client):
    r = client.get("/word")
    assert r.status_code == 200
    words = r.json()
    assert len(words) == 100
    assert words[:3] == ["cat", "dog", "house"]


@pytest.mark.parametrize("count", [0, 1, 5, 100])
def test_count_returns_distinct_known_words(client, count):
    all_words = set(client.get("/word").json())
    words = client.get("/word", params={"count": count}).json()
    assert len(words) == count
    assert len(set(words)) == count
    assert set(words) <= all_words


def test_count_uses_injected_rng(client):
    first = client.get("/word", params={"count": 5}).json()
    second = client.get("/word", params={"count": 5}).json()
    assert first == second  # conftest seeds a fresh Random(42) per request


@pytest.mark.parametrize(
    ("count", "message"),
    [
        (-1, "Count must be non-negative."),
        (101, "Requested number of elements (count) is larger than the size of the array."),
    ],
)
def test_count_out_of_range(client, count, message):
    r = client.get("/word", params={"count": count})
    assert r.status_code == 400
    assert r.json() == {"error": message, "type": "InvalidArgumentException"}


def test_count_not_a_number(client):
    r = client.get("/word", params={"count": "abc"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["query", "count"]


def test_post_accepts_count_as_string(client):
    r = client.post("/word", json={"count": "3"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert len(body["words"]) == 3


def test_post_rejects_unknown_fields(client):
    r = client.post("/word", json={"count": 3, "extra": True})
    assert r.status_code == 422


def test_post_count_too_large(client):
    r = client.post("/word", json={"count": 1000})
    assert r.status_code == 400
    assert r.json()["type"] == "InvalidArgumentException"
