# tests/conftest.py — Fixtures compartidas para tests

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from agent.main import app
from agent.database import engine
from agent.models import Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Crea las tablas antes de todos los tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP para tests de API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    """Cliente autenticado con un tenant de prueba."""
    import uuid
    email = f"test-{uuid.uuid4().hex[:8]}@agentkit.io"
    res = await client.post("/api/auth/register", json={
        "email": email,
        "password": "test123456",
        "name": "Test User",
        "business_name": "Test Business",
    })
    token = res.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
