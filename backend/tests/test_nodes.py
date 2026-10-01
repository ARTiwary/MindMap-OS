import pytest

pytestmark = pytest.mark.asyncio


async def _auth_headers(client, email, username):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "Password123"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_get_node(client):
    headers = await _auth_headers(client, "n1@example.com", "n1user")
    resp = await client.post(
        "/api/v1/nodes", json={"title": "Python", "node_type": "TOPIC"}, headers=headers
    )
    assert resp.status_code == 201
    node = resp.json()
    assert node["title"] == "Python"
    assert node["slug"] == "python"

    resp2 = await client.get(f"/api/v1/nodes/{node['id']}", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["references_count"] == 0


async def test_node_ownership_isolation(client):
    headers_a = await _auth_headers(client, "owner@example.com", "owner")
    headers_b = await _auth_headers(client, "intruder@example.com", "intruder")

    resp = await client.post("/api/v1/nodes", json={"title": "Secret Node"}, headers=headers_a)
    node_id = resp.json()["id"]

    resp_forbidden = await client.get(f"/api/v1/nodes/{node_id}", headers=headers_b)
    assert resp_forbidden.status_code == 404

    resp_delete = await client.delete(f"/api/v1/nodes/{node_id}", headers=headers_b)
    assert resp_delete.status_code == 404


async def test_node_pagination(client):
    headers = await _auth_headers(client, "pager@example.com", "pager")
    for i in range(5):
        await client.post("/api/v1/nodes", json={"title": f"Node {i}"}, headers=headers)

    resp = await client.get("/api/v1/nodes?page=1&limit=2", headers=headers)
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["pages"] == 3


async def test_node_filtering_by_type(client):
    headers = await _auth_headers(client, "filter@example.com", "filterer")
    await client.post("/api/v1/nodes", json={"title": "A Project", "node_type": "PROJECT"}, headers=headers)
    await client.post("/api/v1/nodes", json={"title": "A Note", "node_type": "NOTE"}, headers=headers)

    resp = await client.get("/api/v1/nodes?type=PROJECT", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["node_type"] == "PROJECT"


async def test_search_returns_matching_node_with_tags(client):
    headers = await _auth_headers(client, "searcher@example.com", "searcher")
    tag_resp = await client.post("/api/v1/tags", json={"name": "Backend"}, headers=headers)
    tag_id = tag_resp.json()["id"]
    await client.post(
        "/api/v1/nodes",
        json={"title": "FastAPI Deep Dive", "description": "Async web framework", "tag_ids": [tag_id]},
        headers=headers,
    )

    resp = await client.get("/api/v1/search?q=fastapi", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "FastAPI Deep Dive"
    assert body["items"][0]["tags"][0]["name"] == "Backend"


async def test_pagination_limit_query_param_does_not_override_rate_limit(client):
    """Regression test: the rate-limit dependency must never expose a bare
    `limit` parameter, because FastAPI resolves un-annotated primitive
    dependency parameters as query parameters of the *route*. `/nodes`'s own
    pagination `limit` query param previously collided with the rate
    limiter's `limit` default, so `?limit=2` silently capped the rate limit
    at 2 requests instead of the intended ~100/minute, causing normal
    pagination calls to 429 almost immediately."""
    headers = await _auth_headers(client, "ratelimit-collision@example.com", "ratelimitcollision")
    for i in range(6):
        resp = await client.post("/api/v1/nodes", json={"title": f"RL Node {i}"}, headers=headers)
        assert resp.status_code == 201

    resp = await client.get("/api/v1/nodes?page=1&limit=2", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 6
    assert len(body["items"]) == 2


async def test_update_node(client):
    headers = await _auth_headers(client, "updater@example.com", "updater")
    resp = await client.post("/api/v1/nodes", json={"title": "Draft"}, headers=headers)
    node_id = resp.json()["id"]

    resp2 = await client.patch(
        f"/api/v1/nodes/{node_id}", json={"is_favorite": True, "importance": "HIGH"}, headers=headers
    )
    assert resp2.status_code == 200
    assert resp2.json()["is_favorite"] is True
    assert resp2.json()["importance"] == "HIGH"


async def test_delete_node(client):
    headers = await _auth_headers(client, "deleter@example.com", "deleter")
    resp = await client.post("/api/v1/nodes", json={"title": "Temp"}, headers=headers)
    node_id = resp.json()["id"]

    resp_del = await client.delete(f"/api/v1/nodes/{node_id}", headers=headers)
    assert resp_del.status_code == 204

    resp_get = await client.get(f"/api/v1/nodes/{node_id}", headers=headers)
    assert resp_get.status_code == 404
