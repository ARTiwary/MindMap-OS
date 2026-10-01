import pytest

pytestmark = pytest.mark.asyncio


async def register_and_login(client, email="alice@example.com", username="alice", password="Password123"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password, "full_name": "Alice"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()


async def test_register_creates_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "Password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "bob@example.com"
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "username": "dup1", "password": "Password123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post(
        "/api/v1/auth/register", json={**payload, "username": "dup2"}
    )
    assert resp.status_code == 409


async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "username": "weakpw", "password": "alllowercase"},
    )
    assert resp.status_code == 422


async def test_login_success_returns_tokens(client):
    tokens = await register_and_login(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens


async def test_login_invalid_password_rejected(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "carl@example.com", "username": "carl", "password": "Password123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "carl@example.com", "password": "WrongPass123"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client):
    tokens = await register_and_login(client)
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


async def test_refresh_issues_new_access_token(client):
    tokens = await register_and_login(client)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_rejects_access_token(client):
    tokens = await register_and_login(client)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


async def test_logout_blacklists_access_token(client):
    """Regression test for real JWT revocation: a token must stop working
    the instant logout is called, not just when the frontend discards it
    client-side. Previously logout was a no-op that didn't touch Redis at
    all, so a leaked/copied token stayed valid for its full 15-minute
    lifetime even after the user 'logged out'."""
    tokens = await register_and_login(client, email="revoke@example.com", username="revokeuser")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200

    logout_resp = await client.post("/api/v1/auth/logout", json={}, headers=headers)
    assert logout_resp.status_code == 204

    resp_after = await client.get("/api/v1/auth/me", headers=headers)
    assert resp_after.status_code == 401


async def test_logout_blacklists_refresh_token_when_provided(client):
    tokens = await register_and_login(client, email="revoke2@example.com", username="revokeuser2")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers
    )

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    # The refresh token itself was blacklisted, so minting a fresh access
    # token from it must fail even though the token hasn't naturally expired.
    assert resp.status_code == 401
