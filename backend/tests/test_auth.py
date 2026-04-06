# tests/test_auth.py — Tests de autenticacion

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    res = await client.post("/api/auth/register", json={
        "email": "new@test.com",
        "password": "pass123",
        "name": "New User",
        "business_name": "New Biz",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "tenant_id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "dup@test.com",
        "password": "pass123",
        "name": "User 1",
        "business_name": "Biz 1",
    })
    res = await client.post("/api/auth/register", json={
        "email": "dup@test.com",
        "password": "pass123",
        "name": "User 2",
        "business_name": "Biz 2",
    })
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@test.com",
        "password": "pass123",
        "name": "Login User",
        "business_name": "Login Biz",
    })
    res = await client.post("/api/auth/login", json={
        "email": "login@test.com",
        "password": "pass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "wrong@test.com",
        "password": "pass123",
        "name": "User",
        "business_name": "Biz",
    })
    res = await client.post("/api/auth/login", json={
        "email": "wrong@test.com",
        "password": "wrong",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me(auth_client: AsyncClient):
    res = await auth_client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test User"
    assert data["tenant_name"] == "Test Business"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    res = await client.get("/api/auth/me")
    assert res.status_code in (401, 403)
