# tests/test_api.py — Tests de endpoints generales

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["service"] == "agentkit-saas"


@pytest.mark.asyncio
async def test_conversations_empty(auth_client: AsyncClient):
    res = await auth_client.get("/api/conversations")
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_analytics_empty(auth_client: AsyncClient):
    res = await auth_client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_conversations"] == 0
    assert data["total_messages_today"] == 0


@pytest.mark.asyncio
async def test_webhook_unknown_tenant(client: AsyncClient):
    import uuid
    fake_id = str(uuid.uuid4())
    res = await client.post(f"/webhook/{fake_id}", json={"messages": []})
    assert res.status_code == 404
