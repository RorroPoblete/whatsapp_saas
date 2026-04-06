# tests/test_config.py — Tests de configuracion del agente

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_config(auth_client: AsyncClient):
    res = await auth_client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert data["is_setup_complete"] is False
    assert data["agent_name"] == "Asistente"


@pytest.mark.asyncio
async def test_update_config(auth_client: AsyncClient):
    res = await auth_client.put("/api/config", json={
        "agent_name": "Sofia",
        "agent_tone": "amigable",
        "business_description": "Tienda de ropa",
    })
    assert res.status_code == 200
    assert "agent_name" in res.json()["updated_fields"]

    # Verificar que se guardo
    res = await auth_client.get("/api/config")
    assert res.json()["agent_name"] == "Sofia"


@pytest.mark.asyncio
async def test_generate_prompt(auth_client: AsyncClient):
    # Primero configurar datos del negocio
    await auth_client.put("/api/config", json={
        "agent_name": "Ana",
        "business_name": "Mi Tienda",
        "business_description": "Vendo zapatos",
    })

    res = await auth_client.post("/api/config/generate-prompt")
    assert res.status_code == 200
    prompt = res.json()["system_prompt"]
    assert "Ana" in prompt
    assert "Mi Tienda" in prompt


@pytest.mark.asyncio
async def test_webhook_url(auth_client: AsyncClient):
    res = await auth_client.get("/api/config/webhook-url")
    assert res.status_code == 200
    assert "/webhook/" in res.json()["webhook_url"]


@pytest.mark.asyncio
async def test_update_whatsapp(auth_client: AsyncClient):
    res = await auth_client.put("/api/config/whatsapp", json={
        "provider": "whapi",
        "credentials": {"token": "test-token"},
    })
    assert res.status_code == 200
    assert res.json()["provider"] == "whapi"


@pytest.mark.asyncio
async def test_update_whatsapp_invalid_provider(auth_client: AsyncClient):
    res = await auth_client.put("/api/config/whatsapp", json={
        "provider": "invalid",
        "credentials": {},
    })
    assert res.status_code == 400
