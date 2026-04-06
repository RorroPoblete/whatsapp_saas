# agent/api/config.py — Configuracion del agente (wizard + settings)
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent.database import get_db
from agent.models import TenantConfig, Tenant
from agent.middleware.auth import get_current_tenant_id

router = APIRouter(prefix="/config", tags=["config"])


class ConfigResponse(BaseModel):
    business_name: str
    business_description: str
    business_address: str
    business_phone: str
    business_website: str
    business_hours: dict
    agent_name: str
    agent_tone: str
    use_cases: list
    system_prompt: str
    fallback_message: str
    error_message: str
    knowledge_base: str
    whatsapp_provider: str
    ai_provider: str
    ai_model: str
    is_setup_complete: bool


class ConfigUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    business_address: Optional[str] = None
    business_phone: Optional[str] = None
    business_website: Optional[str] = None
    business_hours: Optional[Dict] = None
    agent_name: Optional[str] = None
    agent_tone: Optional[str] = None
    use_cases: Optional[List] = None
    system_prompt: Optional[str] = None
    fallback_message: Optional[str] = None
    error_message: Optional[str] = None
    knowledge_base: Optional[str] = None


class WhatsAppConfigRequest(BaseModel):
    provider: str
    credentials: dict


class AIConfigRequest(BaseModel):
    provider: str = "openai"
    api_key: str
    model: str = "gpt-4o-mini"


class SetupCompleteRequest(BaseModel):
    system_prompt: str


async def _get_config(tenant_id: uuid.UUID, db: AsyncSession) -> TenantConfig:
    result = await db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuracion no encontrada")
    return config


@router.get("", response_model=ConfigResponse)
async def get_config(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Retorna la configuracion actual del agente."""
    config = await _get_config(tenant_id, db)
    return ConfigResponse(
        business_name=config.business_name,
        business_description=config.business_description,
        business_address=config.business_address,
        business_phone=config.business_phone,
        business_website=config.business_website,
        business_hours=config.business_hours or {},
        agent_name=config.agent_name,
        agent_tone=config.agent_tone,
        use_cases=config.use_cases or [],
        system_prompt=config.system_prompt,
        fallback_message=config.fallback_message,
        error_message=config.error_message,
        knowledge_base=config.knowledge_base,
        whatsapp_provider=config.whatsapp_provider,
        ai_provider=config.ai_provider,
        ai_model=config.ai_model,
        is_setup_complete=config.is_setup_complete,
    )


@router.put("")
async def update_config(
    body: ConfigUpdateRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza la configuracion del agente (campos parciales)."""
    config = await _get_config(tenant_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "ok", "updated_fields": list(update_data.keys())}


@router.put("/whatsapp")
async def update_whatsapp_config(
    body: WhatsAppConfigRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Configura el proveedor de WhatsApp y sus credenciales."""
    config = await _get_config(tenant_id, db)

    if body.provider not in ("whapi", "meta", "twilio"):
        raise HTTPException(status_code=400, detail="Proveedor no soportado: whapi, meta o twilio")

    config.whatsapp_provider = body.provider
    config.whatsapp_credentials = body.credentials
    config.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "ok", "provider": body.provider}


@router.put("/ai")
async def update_ai_config(
    body: AIConfigRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Configura la API key y modelo de IA."""
    config = await _get_config(tenant_id, db)

    config.ai_provider = body.provider
    config.ai_api_key_encrypted = body.api_key  # TODO: encriptar con Fernet
    config.ai_model = body.model
    config.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "ok", "provider": body.provider, "model": body.model}


@router.post("/complete-setup")
async def complete_setup(
    body: SetupCompleteRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Marca el setup como completo y activa el agente."""
    config = await _get_config(tenant_id, db)

    config.system_prompt = body.system_prompt
    config.is_setup_complete = True
    config.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "ok", "message": "Agente activado"}


@router.get("/webhook-url")
async def get_webhook_url(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
):
    """Retorna la URL del webhook que el tenant debe configurar en su proveedor."""
    base_url = "https://tu-dominio.com"  # TODO: configurar desde env
    return {
        "webhook_url": f"{base_url}/webhook/{tenant_id}",
        "instructions": "Configura esta URL en tu proveedor de WhatsApp como webhook de mensajes entrantes (POST).",
    }


@router.post("/generate-prompt")
async def generate_system_prompt(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Genera automaticamente el system prompt basado en la config del negocio."""
    config = await _get_config(tenant_id, db)

    # Generar prompt basado en los datos del negocio
    tono_desc = {
        "profesional": "profesional y formal, usando un lenguaje corporativo",
        "amigable": "amigable y casual, como un amigo que ayuda",
        "vendedor": "persuasivo y orientado a ventas, destacando beneficios",
        "empatico": "empatico y calido, mostrando genuina preocupacion",
    }

    use_cases_text = ""
    for uc in (config.use_cases or []):
        use_cases_text += f"  - {uc}\n"

    horario_text = ""
    for dia, horas in (config.business_hours or {}).items():
        horario_text += f"  - {dia}: {horas}\n"

    prompt = f"""Eres {config.agent_name}, el asistente virtual de {config.business_name}.

## Tu identidad
- Te llamas {config.agent_name}
- Representas a {config.business_name}
- Tu tono es {tono_desc.get(config.agent_tone, config.agent_tone)}

## Sobre el negocio
{config.business_description}
{f"Direccion: {config.business_address}" if config.business_address else ""}
{f"Telefono: {config.business_phone}" if config.business_phone else ""}
{f"Web: {config.business_website}" if config.business_website else ""}

## Tus capacidades
{use_cases_text if use_cases_text else "  - Responder preguntas sobre el negocio"}

{f"## Informacion del negocio{chr(10)}{config.knowledge_base}" if config.knowledge_base else ""}

## Horario de atencion
{horario_text if horario_text else "No especificado"}
Fuera de horario responde: "Gracias por escribirnos. Te responderemos en cuanto estemos disponibles."

## Reglas de comportamiento
- SIEMPRE responde en espanol
- Se {config.agent_tone} en cada mensaje
- Si no sabes algo, di: "No tengo esa informacion, pero dejame conectarte con alguien de nuestro equipo."
- NUNCA inventes informacion que no te hayan proporcionado
- Manten las respuestas concisas pero utiles
- Si el cliente parece frustrado, muestra empatia antes de resolver
- Termina los mensajes con una pregunta o call-to-action cuando sea apropiado"""

    config.system_prompt = prompt
    config.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "ok", "system_prompt": prompt}
