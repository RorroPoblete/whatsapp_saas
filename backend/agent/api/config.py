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
    niche: str
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
    onboarding_questions: list
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
    onboarding_questions: Optional[List] = None
    niche: Optional[str] = None


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
        niche=config.niche,
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
        onboarding_questions=config.onboarding_questions or [],
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
    """Marca el setup como completo, asigna numero WhatsApp del pool y activa el agente."""
    from agent.api.numbers import assign_number_to_tenant

    config = await _get_config(tenant_id, db)
    config.system_prompt = body.system_prompt
    config.is_setup_complete = True
    config.updated_at = datetime.utcnow()

    # Asignar numero del pool si no tiene uno
    assigned_number = None
    if not config.whatsapp_credentials or not config.whatsapp_credentials.get("token"):
        number = await assign_number_to_tenant(tenant_id, db)
        if number:
            assigned_number = number.phone_number

    await db.commit()

    return {
        "status": "ok",
        "message": "Agente activado",
        "phone_number": assigned_number,
    }


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


# ── Auto-setup: genera TODO desde descripcion + URL ───────

class AutoSetupRequest(BaseModel):
    description: str
    url: Optional[str] = None


@router.post("/auto-setup")
async def auto_setup(
    body: AutoSetupRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Recibe descripcion del negocio + URL opcional.
    Scrapea la web, analiza todo con IA y genera:
    system prompt, servicios, recursos, agent name, tone.
    NO aplica cambios — retorna la sugerencia para review.
    """
    import os
    config = await _get_config(tenant_id, db)
    api_key = config.ai_api_key_encrypted or os.getenv("PLATFORM_OPENAI_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key de IA no disponible")

    # 1. Obtener info del sitio web si hay URL
    web_info = ""
    if body.url:
        try:
            from agent.scraper import fetch_url_text
            web_info = await fetch_url_text(body.url)
        except Exception as e:
            web_info = f"(No se pudo acceder a la URL: {e})"

    # 2. Llamar a IA para generar todo de una vez
    from openai import AsyncOpenAI
    import json, re

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2000,
        messages=[
            {"role": "system", "content": """Eres un experto configurando agentes de WhatsApp con IA para negocios.

Te dan una descripcion del negocio y opcionalmente el contenido de su sitio web.
Debes generar UNA configuracion completa.

Responde SOLO con JSON valido (sin markdown, sin ```):
{
  "agent_name": "nombre del asistente (ej: Isabella, Sofia, Carlos)",
  "agent_tone": "profesional|amigable|vendedor|empatico",
  "business_name": "nombre del negocio",
  "business_description": "descripcion breve",
  "business_phone": "telefono si lo encuentras",
  "business_website": "url del sitio",
  "business_address": "direccion si la encuentras",
  "business_hours": {"Lunes a Viernes": "9:00 - 18:00", "Sabado": "10:00 - 14:00", "Domingo": "Cerrado"},
  "system_prompt": "El system prompt completo para el agente. Incluye: identidad, info del negocio, servicios con precios, reglas de comportamiento. Debe ser exhaustivo con toda la info encontrada. NO uses markdown ni emojis. Las reglas deben incluir: responder corto (2-3 oraciones), no inventar datos, invitar a profundizar.",
  "services": [
    {
      "name": "nombre del servicio (ej: Restaurant, Hotel, Consulta Medica)",
      "niche": "restaurant|hotel|agenda|custom",
      "resources": [
        {"name": "nombre recurso", "type": "table|room|slot|custom", "capacity": 2, "duration_minutes": 90, "description": "desc corta"}
      ]
    }
  ]
}

Reglas:
- El system_prompt debe ser COMPLETO y listo para usar, con toda la info del negocio
- Si detectas servicios reservables (mesas, habitaciones, citas), genera los recursos
- Restaurant: mesas con capacidades variadas (2,4,6), duracion 90 min
- Hotel: habitaciones por tipo, duracion 1440 min (1 noche)
- Agenda/Citas: slots de hora, duracion 30-60 min
- Si hay multiples servicios, incluye TODOS
- Si no hay servicios reservables, services = []
- Incluye TODOS los precios, horarios, contactos que encuentres"""},
            {"role": "user", "content": f"DESCRIPCION DEL NEGOCIO:\n{body.description}\n\n{'CONTENIDO DEL SITIO WEB:' + chr(10) + web_info if web_info else '(Sin sitio web)'}"}
        ],
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

    result = json.loads(text)
    return result


@router.post("/apply-setup")
async def apply_setup(
    body: dict,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Aplica la configuracion generada por auto-setup.
    Actualiza config, crea servicios y recursos.
    """
    from agent.models import Service, Resource

    config = await _get_config(tenant_id, db)

    # Actualizar config del tenant (usar "" como default si viene null)
    for field in ["agent_name", "agent_tone", "business_name", "business_description",
                  "business_phone", "business_website", "business_address", "system_prompt"]:
        value = body.get(field)
        setattr(config, field, value if value is not None else "")

    if "business_hours" in body:
        config.business_hours = body["business_hours"]

    config.updated_at = datetime.utcnow()

    # Crear servicios y recursos
    created_services = []
    for svc_data in body.get("services", []):
        service = Service(
            tenant_id=tenant_id,
            name=svc_data.get("name", "Servicio"),
            niche=svc_data.get("niche", "custom"),
        )
        db.add(service)
        await db.flush()

        for r in svc_data.get("resources", []):
            db.add(Resource(
                tenant_id=tenant_id, service_id=service.id,
                name=r["name"], resource_type=r.get("type", "custom"),
                capacity=r.get("capacity", 1),
                duration_minutes=r.get("duration_minutes", 60),
                description=r.get("description", ""),
            ))
        created_services.append({"name": service.name, "resources": len(svc_data.get("resources", []))})

    await db.commit()
    return {"status": "ok", "services_created": created_services}
