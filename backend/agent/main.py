# agent/main.py — Servidor FastAPI multi-tenant
from __future__ import annotations

"""
Servidor principal de AgentKit SaaS.
- API REST para el frontend (auth, config, conversations, analytics)
- Webhook multi-tenant: POST /webhook/{tenant_id}
"""

import os
import uuid
import logging
from datetime import datetime, date
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import select

from agent.database import init_db, async_session
from agent.models import TenantConfig, Conversation, Message, UsageTracking, WebhookLog
from agent.brain import generar_respuesta
from agent.providers import obtener_proveedor

# API Routers
from agent.api.auth import router as auth_router
from agent.api.config import router as config_router
from agent.api.conversations import router as conversations_router
from agent.api.analytics import router as analytics_router

load_dotenv()

# Logging
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("agentkit")
logger.setLevel(logging.DEBUG if ENVIRONMENT == "development" else logging.INFO)

PORT = int(os.getenv("PORT", 8000))

# Cache de configs de tenants (evita leer DB en cada mensaje)
_tenant_cache: dict[uuid.UUID, TenantConfig] = {}


async def _get_tenant_config(tenant_id: uuid.UUID) -> TenantConfig | None:
    """Obtiene config del tenant con cache en memoria."""
    if tenant_id in _tenant_cache:
        return _tenant_cache[tenant_id]

    async with async_session() as session:
        result = await session.execute(
            select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
        )
        config = result.scalar_one_or_none()
        if config:
            _tenant_cache[tenant_id] = config
        return config


async def _get_or_create_conversation(
    session, tenant_id: uuid.UUID, phone_number: str
) -> Conversation:
    """Obtiene o crea una conversacion para un telefono."""
    result = await session.execute(
        select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.phone_number == phone_number,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(tenant_id=tenant_id, phone_number=phone_number)
        session.add(conv)
        await session.flush()
    return conv


async def _update_usage(session, tenant_id: uuid.UUID, tokens_in: int, tokens_out: int):
    """Incrementa contadores de uso del tenant para hoy."""
    today = date.today()
    result = await session.execute(
        select(UsageTracking).where(
            UsageTracking.tenant_id == tenant_id,
            UsageTracking.date == today,
        )
    )
    usage = result.scalar_one_or_none()
    if not usage:
        usage = UsageTracking(tenant_id=tenant_id, date=today)
        session.add(usage)
        await session.flush()

    usage.messages_received += 1
    usage.messages_sent += 1
    usage.ai_tokens_input += tokens_in
    usage.ai_tokens_output += tokens_out
    usage.whatsapp_api_calls += 1


# ════════════════════════════════════════════════════════════
# App FastAPI
# ════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info(f"AgentKit SaaS corriendo en puerto {PORT}")
    yield
    _tenant_cache.clear()


app = FastAPI(
    title="AgentKit — WhatsApp AI Agent Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS para el frontend
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers de API
app.include_router(auth_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "agentkit-saas", "version": "2.0.0"}


# ════════════════════════════════════════════════════════════
# Webhook multi-tenant
# ════════════════════════════════════════════════════════════

@app.get("/webhook/{tenant_id}")
async def webhook_verificacion(tenant_id: uuid.UUID, request: Request):
    """Verificacion GET del webhook (requerido por Meta Cloud API)."""
    config = await _get_tenant_config(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    proveedor = obtener_proveedor(config.whatsapp_provider, config.whatsapp_credentials)
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook/{tenant_id}")
async def webhook_handler(tenant_id: uuid.UUID, request: Request):
    """
    Webhook multi-tenant: recibe mensajes de WhatsApp de cualquier tenant.
    Cada tenant configura su URL como: POST /webhook/{su-tenant-id}
    """
    config = await _get_tenant_config(tenant_id)
    if not config or not config.is_setup_complete:
        raise HTTPException(status_code=404, detail="Tenant no encontrado o no configurado")

    proveedor = obtener_proveedor(config.whatsapp_provider, config.whatsapp_credentials)

    try:
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            if msg.es_propio or not msg.texto:
                continue

            logger.info(f"[{tenant_id}] Mensaje de {msg.telefono}: {msg.texto}")

            async with async_session() as session:
                # Log del webhook
                session.add(WebhookLog(
                    tenant_id=tenant_id,
                    provider=config.whatsapp_provider,
                    payload={"telefono": msg.telefono, "texto": msg.texto},
                    processed=True,
                ))

                # Obtener o crear conversacion
                conv = await _get_or_create_conversation(session, tenant_id, msg.telefono)

                # Verificar que la IA este activa para esta conversacion
                if not conv.is_ai_active:
                    logger.info(f"[{tenant_id}] IA desactivada para {msg.telefono}")
                    await session.commit()
                    continue

                # Obtener historial
                msg_query = (
                    select(Message)
                    .where(Message.conversation_id == conv.id)
                    .order_by(Message.created_at.desc())
                    .limit(20)
                )
                result = await session.execute(msg_query)
                historial_msgs = list(reversed(result.scalars().all()))
                historial = [{"role": m.role, "content": m.content} for m in historial_msgs]

                # Generar respuesta con IA
                resultado = await generar_respuesta(
                    mensaje=msg.texto,
                    historial=historial,
                    system_prompt=config.system_prompt,
                    ai_api_key=config.ai_api_key_encrypted,
                    ai_model=config.ai_model,
                    fallback_message=config.fallback_message,
                    error_message=config.error_message,
                    custom_tools=config.custom_tools,
                )

                respuesta = resultado["respuesta"]

                # Guardar mensajes
                session.add(Message(
                    tenant_id=tenant_id, conversation_id=conv.id,
                    role="user", content=msg.texto,
                ))
                session.add(Message(
                    tenant_id=tenant_id, conversation_id=conv.id,
                    role="assistant", content=respuesta,
                ))

                conv.last_message_at = datetime.utcnow()

                # Tracking de uso
                await _update_usage(
                    session, tenant_id,
                    resultado["tokens_input"], resultado["tokens_output"],
                )

                await session.commit()

            # Enviar respuesta por WhatsApp
            await proveedor.enviar_mensaje(msg.telefono, respuesta)
            logger.info(f"[{tenant_id}] Respuesta a {msg.telefono}: {respuesta[:80]}...")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"[{tenant_id}] Error en webhook: {e}")
        async with async_session() as session:
            session.add(WebhookLog(
                tenant_id=tenant_id, provider=config.whatsapp_provider,
                payload={}, processed=False, error=str(e),
            ))
            await session.commit()
        raise HTTPException(status_code=500, detail=str(e))
