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


async def _create_node(client, headers, title):
    resp = await client.post("/api/v1/nodes", json={"title": title}, headers=headers)
    return resp.json()["id"]


async def test_create_relationship(client):
    headers = await _auth_headers(client, "rel1@example.com", "rel1")
    a = await _create_node(client, headers, "FastAPI")
    b = await _create_node(client, headers, "Python")

    resp = await client.post(
        "/api/v1/relationships",
        json={"source_node_id": a, "target_node_id": b, "relationship_type": "REQUIRES"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["relationship_type"] == "REQUIRES"


async def test_self_reference_rejected(client):
    headers = await _auth_headers(client, "rel2@example.com", "rel2")
    a = await _create_node(client, headers, "Solo Node")

    resp = await client.post(
        "/api/v1/relationships", json={"source_node_id": a, "target_node_id": a}, headers=headers
    )
    assert resp.status_code == 400


async def test_duplicate_relationship_rejected(client):
    headers = await _auth_headers(client, "rel3@example.com", "rel3")
    a = await _create_node(client, headers, "A")
    b = await _create_node(client, headers, "B")

    payload = {"source_node_id": a, "target_node_id": b, "relationship_type": "RELATED_TO"}
    resp1 = await client.post("/api/v1/relationships", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/relationships", json=payload, headers=headers)
    assert resp2.status_code == 409


async def test_relationship_requires_node_ownership(client):
    headers_a = await _auth_headers(client, "rel4a@example.com", "rel4a")
    headers_b = await _auth_headers(client, "rel4b@example.com", "rel4b")

    a = await _create_node(client, headers_a, "Owner Node A")
    b = await _create_node(client, headers_a, "Owner Node B")

    resp = await client.post(
        "/api/v1/relationships",
        json={"source_node_id": a, "target_node_id": b},
        headers=headers_b,
    )
    assert resp.status_code == 404


async def test_delete_relationship(client):
    headers = await _auth_headers(client, "rel5@example.com", "rel5")
    a = await _create_node(client, headers, "X")
    b = await _create_node(client, headers, "Y")
    resp = await client.post(
        "/api/v1/relationships", json={"source_node_id": a, "target_node_id": b}, headers=headers
    )
    rel_id = resp.json()["id"]

    resp_del = await client.delete(f"/api/v1/relationships/{rel_id}", headers=headers)
    assert resp_del.status_code == 204
