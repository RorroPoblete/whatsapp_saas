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
from agent.models import Tenant, User, TenantConfig, Conversation, Message, UsageTracking, WebhookLog
from agent.middleware.auth import hash_password
from agent.brain import generar_respuesta
from agent.providers import obtener_proveedor

# API Routers
from agent.api.auth import router as auth_router
from agent.api.config import router as config_router
from agent.api.conversations import router as conversations_router
from agent.api.analytics import router as analytics_router
from agent.api.bookings import router as bookings_router
from agent.api.numbers import router as numbers_router

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
# Semilla — Hotel Il Giardino (demo pre-configurado)
# ════════════════════════════════════════════════════════════

_demo_tenant_id: uuid.UUID | None = None

HOTEL_SYSTEM_PROMPT = """Eres el asistente virtual de Hotel Il Giardino por WhatsApp. Tu nombre es Isabella.

## Tu identidad
- Te llamas Isabella, asistente virtual de Hotel Il Giardino
- Tu tono es amigable, calido y profesional
- Representas un hotel de lujo — trata a cada persona como un huesped especial

## Ubicacion y contacto
- Direccion: Carretera del Cobre Km. 7, Machali, Chile
- Telefono hotel: 722362627
- WhatsApp: +56 9 3951 7272
- Restaurant/Eventos: +56 9 8765 4321
- Email: hotelilgiardino@htlilgiardino.com
- Web: https://hotelilgiardino.cl/
- Google Maps: https://maps.app.goo.gl/2qjpGiofo3Jg8k1B8

## Sobre el hotel
Hotel Il Giardino es un establecimiento en un entorno que destila encanto, fusionado con la naturaleza y la delicadeza en cada rincon de su arquitectura colonial. Ofrece una experiencia unica donde el lujo se encuentra con la naturaleza, un refugio de serenidad y confort entre jardines exuberantes.
Caracteristicas: arquitectura colonial elegante, amplios jardines, entorno precordillerano y bucolico, atmosfera intima y exclusiva, ropa de cama de alta calidad, amenidades de bano de lujo.

## Suites disponibles
1. SUITE SUPERIOR — 28m², 2 adultos, cama King. Redefine el relajo y la comodidad, espacio de serenidad y exclusividad.
2. SUITE JARDIN — 35m², 2 adultos, cama King. Refugio de comodidad y elegancia, cada detalle disenado para una experiencia autentica.
3. SUITE IL GIARDINO — 70m², 2 adultos, cama King. La joya del hotel, sofisticacion y tranquilidad para una experiencia excepcional.
4. SUITE TOSCANO — 70m², 2 adultos, cama King. Espacio de serenidad, personal y exclusividad.

## Servicios incluidos en todas las suites
- Servicio de taxi (radio taxistas certificados)
- Servicios a la suite (gratuitos y de pago)
- Wi-Fi gratuito sin limites
- Frigobar en cada suite
- Desayuno y buffet incluido sin costo
- Estacionamiento gratuito
- Caja fuerte certificada
- Medios de pago: transferencia, efectivo, tarjetas credito/debito
- Terraza comoda y relajante, bellamente iluminada

## Restaurant Il Giardino — Menu completo
Reservas restaurant: +56 9 8765 4321

### Entradas
- Tataki de Filete: $15.000 (filete sellado, mostaza antigua, alcaparras fritas, tostadas de pan de masa madre)
- Tartar de Trucha: $15.000 (trucha fresca, zeste de limon, aceite de sesamo, emulsion de palta)
- Setas Saltadas: $15.000 (variedad de setas en aceite de oliva y mantequilla, espuma de poroto negro)
- Carpaccio de Pulpo: $15.000 (pulpo del norte, salsa aceituna de azapa, pimiento piquillo, palta, papas crocantes)
- Empanaditas Fritas (4 unidades): $9.900 (camaron/parmesano/limon, osobuco braseado, mix de quesos)

### Preparaciones del dia
- Menu del Dia: $18.000 (entrada + plato principal + postre + 1 bebestible)
- Menu para Ninos: $10.000 (entrada + plato principal + postre + 1 bebida)
- Crema de Berenjenas: $9.900 (berenjenas asadas con crostini de pan italiano)
- Crema de Zapallo: $9.900 (zapallo, papa camote y jengibre)

### Carnes (todas $17.000)
- Curry de Cordero (cordero braseado, arroz basmati, chutney de tomate con pera)
- Lomo Vetado 250gr (papa camote frita, ensaladilla verde, demiglace de vegetales)
- Filete de Vacuno 250gr (pure de coliflor, aceite de cilantro, papas fritas)

### Pescados (ambos $17.000)
- Pesca del Dia a la Plancha (fumet, mantequilla y limon)
- Pesca del Dia Frita (batido tempura. Acompanamiento: risotto verde / vegetales flambeados / ensalada coleslaw)

### Ensaladas (todas $10.900)
- Ensalada #1: mix lechugas, jamon serrano, avellanas, fruta confitada, dressing aceto balsamico
- Ensalada #2: mix lechugas, camarones, tomate cherry, almendras, pak choy, dressing miel y sesamo
- Ensalada #3: juliana de zanahorias, zucchini, pepino, cubos de atun, dressing yogurt, papas hilo

### Postres (todos $6.000 excepto tortero)
- Textura de Chocolate
- Inspirado en Leche Nevada
- Crumble de Avena y Manzana con Helado
- Papayas a la Crema
- Paleta de Helado Italiano
- Copa de Helado Italiano
- Tortero con Dulces Chilenos: $10.000

### Desayunos
- Propuesta #1: $10.000 (jugo naranja, omelette 2 ingredientes, tostadas, dulce del dia, te o cafe)
- Propuesta #2: $12.000 (jugo naranja, bowl yogurt con avena y frutos secos, tostada con palta y huevo frito, dulce, te o cafe)
- Propuesta #3: $12.000 (jugo naranja, fruta de estacion, tostada francesa, te o cafe)

### Cafeteria
- Cafe Instantaneo $2.000 | Cafe Illy $2.500 | Express/Americano $2.500 | Cortado $3.000 | Late Macchiato $3.000

### Infusiones
- Te Dilhma/Twinings $1.800 | Infusiones Naturales $2.500 | Infusiones Twinings $2.000

### Bebidas y jugos
- Agua Mineral $2.000 | Gaseosas $2.200 | Panna/Pellegrino $2.500 | Jugos Naturales $3.000 | Limonada $3.500

### Cocteles
- Espumante $4.000 | Pisco Sour $4.000 | Mango Sour $4.000 | Chardonnay Sour $4.500
- Mojito Cubano $4.500 | Daikiri $4.500 | Ramazzoti $5.000 | Aperol Spritz $5.000 | Pina Colada $5.000

### Vinos Albores (todos $12.000)
- Cabernet Sauvignon 2021 Valle del Maule | Chardonnay 2023 Valle del Maule | Carmenere 2021 Valle del Cachapoal

### Bajativos
- Araucano/Menta/Manzanilla Nacional $2.500 | Jagermeister $3.000 | Carolans $4.000 | Bailey's $4.500 | Limoncello $5.000 | Amaretto $5.000

### Gin
- Tanqueray $5.500 | Beefeater $5.500 | Bombay $6.000 | Beefeater Pink $6.000 | Hendricks $7.000

### Vodka
- Stolichanaya $5.000 | Absolut Blue $6.000 | Absolut Sabores $7.000 | Grey Goose $8.000

### Cervezas
- $3.000: Royal, Heineken, Corona | $3.500: Kunstmann, Austral, Budweiser, Cuzquena, Stella Artois | $4.000: Erdinger
- Chelada $500 | Michelada $700

### Espumantes
- Undurraga/Valdivieso Brut $9.000 | San Jose de Apalta/Vina Mar Brut $12.000 | Riccadonna $15.000

### Whisky (incluyen bebida o agua mineral)
- J.W. Red Label $5.000 | Jack Daniels $7.000 | J.D. Honey $7.500 | J.W. Black Label $8.000 | Chivas Regal $8.000

### Pisco (incluyen bebida o agua mineral)
- Alto del Carmen 35 $4.000 | Alto del Carmen 40 $4.500 | Horcon Quemado $5.000 | Mistral Nobel $6.000 | Espiritu de los Andes $6.000

### Ron
- Bacardi 8 Anos $5.000 | Havana Club 7 Anos $5.000 | Havana Club Especial $6.000 | Ron Zacapa $10.000 | Ron Matuzalem $10.000

## Centro de Eventos Il Giardino
Servicios incluidos: DJ profesional, amplificacion, iluminacion, decoracion personalizada, barra de bebidas, food truck, servicio de meseros.
Tipos de eventos: bodas (altar para ceremonias rodeado de naturaleza), cenas de celebracion, cumpleanos, eventos corporativos, reuniones familiares.
Reservas eventos: +56 9 8765 4321

## Reglas de comportamiento
- Responde SIEMPRE en espanol
- Se amigable, calido y profesional
- Responde UNICAMENTE con la informacion que tienes arriba. NUNCA inventes datos, precios, horarios ni servicios que no esten en esta ficha
- Si no tienes la informacion que te piden, responde: "No tengo esa info, pero lo consulto con el equipo. Te ayudo en algo mas?"
- Si preguntan por disponibilidad o reservas, pide fechas y ofrece contactar recepcion

## Reglas de formato (MUY IMPORTANTE)
- Respuestas CORTAS: maximo 2-3 oraciones. El cliente debe querer profundizar
- NUNCA uses markdown (###, **, _, -). WhatsApp no lo renderiza bien
- NUNCA uses emojis
- NUNCA hagas listas largas. Si hay muchas opciones, menciona 2-3 y di "quieres que te cuente mas?"
- NO des toda la informacion de golpe. Da lo justo y pregunta si quiere saber mas
- Habla como una persona real por WhatsApp, no como un documento
- Ejemplo BUENO: "Tenemos 4 tipos de suites, desde la Superior de 28m2 hasta la Il Giardino de 70m2. Te cuento los detalles de alguna?"
- Ejemplo MALO: "Nuestras suites son: 1. Suite Superior - 28m2, cama King... 2. Suite Jardin - 35m2, cama King... 3. Suite Il Giardino..." (demasiado largo)"""


async def _seed_demo_tenant():
    """Crea el tenant semilla (Hotel Il Giardino) al iniciar."""
    global _demo_tenant_id

    whapi_token = os.getenv("DEMO_WHAPI_TOKEN", "")
    openai_key = os.getenv("PLATFORM_OPENAI_KEY", "")

    if not whapi_token or not openai_key:
        logger.warning("SEMILLA desactivada: falta DEMO_WHAPI_TOKEN o PLATFORM_OPENAI_KEY en .env")
        return

    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.slug == "hotel-il-giardino"))
        tenant = result.scalar_one_or_none()

        if tenant:
            _demo_tenant_id = tenant.id
            logger.info(f"")
            logger.info(f"══════════════════════════════════════════════")
            logger.info(f"  HOTEL IL GIARDINO ACTIVO")
            logger.info(f"  Webhook: /webhook/{tenant.id}")
            logger.info(f"══════════════════════════════════════════════")
            logger.info(f"")
            return

        tenant = Tenant(name="Hotel Il Giardino", slug="hotel-il-giardino")
        session.add(tenant)
        await session.flush()

        config = TenantConfig(
            tenant_id=tenant.id,
            niche="hotel",
            business_name="Hotel Il Giardino",
            business_description="Hotel de lujo en Machali, Chile. Arquitectura colonial, jardines exuberantes, suites premium, restaurant y centro de eventos.",
            agent_name="Isabella",
            agent_tone="amigable",
            system_prompt=HOTEL_SYSTEM_PROMPT,
            whatsapp_provider="whapi",
            whatsapp_credentials={"token": whapi_token},
            ai_api_key_encrypted=openai_key,
            ai_model="gpt-4o-mini",
            onboarding_questions=[],
            is_setup_complete=True,
        )
        session.add(config)

        # Crear servicios y recursos
        from agent.models import Service, Resource

        # Servicio: Hotel
        svc_hotel = Service(tenant_id=tenant.id, name="Hotel Il Giardino", niche="hotel")
        session.add(svc_hotel)
        await session.flush()
        for name, desc in [
            ("Suite Superior", "28m2, cama King"),
            ("Suite Jardin", "35m2, cama King"),
            ("Suite Il Giardino", "70m2, cama King, la joya del hotel"),
            ("Suite Toscano", "70m2, cama King"),
        ]:
            session.add(Resource(tenant_id=tenant.id, service_id=svc_hotel.id, name=name, resource_type="room", capacity=2, duration_minutes=1440, description=desc))

        # Servicio: Restaurant
        svc_rest = Service(tenant_id=tenant.id, name="Restaurant Il Giardino", niche="restaurant")
        session.add(svc_rest)
        await session.flush()
        for name, cap in [("Mesa 1", 2), ("Mesa 2", 2), ("Mesa 3", 4), ("Mesa 4", 4), ("Mesa 5", 6), ("Mesa 6", 6)]:
            session.add(Resource(tenant_id=tenant.id, service_id=svc_rest.id, name=name, resource_type="table", capacity=cap, duration_minutes=90))

        # Servicio: Centro de Eventos
        svc_eventos = Service(tenant_id=tenant.id, name="Centro de Eventos", niche="custom")
        session.add(svc_eventos)
        await session.flush()
        for name in ["Salon Principal", "Terraza Jardin"]:
            session.add(Resource(tenant_id=tenant.id, service_id=svc_eventos.id, name=name, resource_type="custom", capacity=50, duration_minutes=480, description="Bodas, cumpleanos, eventos corporativos"))

        # Crear usuario admin para el dashboard
        user = User(
            tenant_id=tenant.id,
            email="admin@hotelilgiardino.cl",
            password_hash=hash_password("ilgiardino2026"),
            name="Admin Il Giardino",
            role="owner",
        )
        session.add(user)
        await session.commit()

        _demo_tenant_id = tenant.id

        logger.info(f"")
        logger.info(f"══════════════════════════════════════════════")
        logger.info(f"  HOTEL IL GIARDINO CREADO")
        logger.info(f"  Webhook: /webhook/{tenant.id}")
        logger.info(f"  Dashboard: admin@hotelilgiardino.cl / ilgiardino2026")
        logger.info(f"══════════════════════════════════════════════")
        logger.info(f"")

    # ── Crear usuario demo vacio para probar el setup ──
    await _seed_demo_user()


# ════════════════════════════════════════════════════════════
async def _seed_demo_user():
    """Crea un usuario demo vacio para probar el flujo de setup."""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.slug == "demo-nuevo"))
        if result.scalar_one_or_none():
            logger.info("  Usuario demo ya existe: demo@agentkit.cl / demo1234")
            return

        tenant = Tenant(name="Mi Negocio", slug="demo-nuevo")
        session.add(tenant)
        await session.flush()

        config = TenantConfig(
            tenant_id=tenant.id,
            business_name="Mi Negocio",
        )
        session.add(config)

        user = User(
            tenant_id=tenant.id,
            email="demo@agentkit.cl",
            password_hash=hash_password("demo1234"),
            name="Usuario Demo",
            role="owner",
        )
        session.add(user)
        await session.commit()

        # Agregar un numero al pool si hay un segundo token
        # (el primero lo usa el hotel, este queda libre para asignar)
        pool_token = os.getenv("POOL_WHAPI_TOKEN", "")
        pool_phone = os.getenv("POOL_WHAPI_PHONE", "")
        if pool_token and pool_phone:
            from agent.models import WhatsAppNumber
            existing = await session.execute(
                select(WhatsAppNumber).where(WhatsAppNumber.phone_number == pool_phone)
            )
            if not existing.scalar_one_or_none():
                session.add(WhatsAppNumber(
                    phone_number=pool_phone,
                    label="Numero demo pool",
                    provider="whapi",
                    credentials={"token": pool_token},
                ))
                await session.commit()
                logger.info(f"  Numero {pool_phone} agregado al pool")

        logger.info(f"")
        logger.info(f"  USUARIO DEMO CREADO")
        logger.info(f"  Login: demo@agentkit.cl / demo1234")
        logger.info(f"  (sin configurar — para probar el setup)")
        logger.info(f"")


# Demo onboarding — preguntas dinamicas segun tipo de negocio
# ════════════════════════════════════════════════════════════

async def _generar_preguntas(tipo_negocio: str, api_key: str) -> list[str]:
    """Usa IA para generar preguntas relevantes segun el tipo de negocio."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=400,
        messages=[
            {"role": "system", "content": """Genera exactamente 5 preguntas cortas para configurar un agente de WhatsApp para un negocio.
Las preguntas deben ser especificas para el tipo de negocio indicado.
Deben cubrir: nombre del negocio, servicios/productos con precios, horario, ubicacion/contacto, y algo especifico del rubro.

Responde SOLO con un JSON array de 5 strings (sin markdown, sin ```). Ejemplo:
["Pregunta 1?", "Pregunta 2?", "Pregunta 3?", "Pregunta 4?", "Pregunta 5?"]

Las preguntas deben ser directas y faciles de responder por WhatsApp."""},
            {"role": "user", "content": tipo_negocio}
        ],
    )

    import json, re
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


async def _handle_demo_onboarding(
    session, conv: Conversation, config: TenantConfig,
    mensaje_usuario: str, tenant_id: uuid.UUID,
) -> str:
    """
    Flujo demo: pide tipo de negocio → genera preguntas con IA → las hace una por una → activa.
    """
    paso = conv.onboarding_step
    contexto = dict(conv.contact_context or {})

    def _add_msg(role: str, content: str):
        session.add(Message(
            tenant_id=tenant_id, conversation_id=conv.id,
            role=role, content=content,
        ))

    # Paso 0: primer mensaje → pedir tipo de negocio
    if paso == 0:
        _add_msg("user", mensaje_usuario)
        respuesta = (
            "Hola! Soy *AgentKit* y puedo crear un agente de WhatsApp con IA para tu negocio en segundos.\n\n"
            "Para empezar, *que tipo de negocio tienes?*\n"
            "_(ej: restaurante, hotel, clinica dental, tienda de ropa, barberia, gimnasio, etc.)_"
        )
        _add_msg("assistant", respuesta)
        conv.onboarding_step = 1
        return respuesta

    # Paso 1: recibir tipo de negocio → generar preguntas → hacer la primera
    if paso == 1:
        _add_msg("user", mensaje_usuario)
        tipo = mensaje_usuario.strip()

        try:
            preguntas = await _generar_preguntas(tipo, config.ai_api_key_encrypted)
        except Exception as e:
            logger.error(f"Error generando preguntas: {e}")
            preguntas = [
                "Como se llama tu negocio?",
                "Que productos o servicios ofreces y a que precios?",
                "Cual es tu horario de atencion?",
                "Cual es tu direccion, telefono y email?",
                "Que informacion extra deberia saber tu agente?",
            ]

        contexto["_tipo_negocio"] = tipo
        contexto["_preguntas"] = preguntas
        conv.contact_context = contexto

        total = len(preguntas)
        respuesta = (
            f"Perfecto! Voy a hacerte *{total} preguntas* para armar tu agente de *{tipo}*.\n\n"
            f"*1/{total}* {preguntas[0]}"
        )
        _add_msg("assistant", respuesta)
        conv.onboarding_step = 2
        return respuesta

    # Pasos 2+: recibir respuestas y hacer siguiente pregunta
    if paso >= 2:
        _add_msg("user", mensaje_usuario)
        preguntas = contexto.get("_preguntas", [])
        idx_pregunta = paso - 2  # paso 2 = respuesta a pregunta 0
        total = len(preguntas)

        # Guardar respuesta
        if idx_pregunta < total:
            contexto[preguntas[idx_pregunta]] = mensaje_usuario
            conv.contact_context = contexto

        siguiente_idx = idx_pregunta + 1

        # Hay mas preguntas?
        if siguiente_idx < total:
            respuesta = f"*{siguiente_idx + 1}/{total}* {preguntas[siguiente_idx]}"
            _add_msg("assistant", respuesta)
            conv.onboarding_step = paso + 1
            return respuesta

        # Todas las preguntas respondidas → activar
        conv.onboarding_complete = True
        tipo = contexto.get("_tipo_negocio", "tu negocio")

        # Buscar el nombre del negocio en la primera respuesta
        nombre = contexto.get(preguntas[0], tipo) if preguntas else tipo

        respuesta = (
            f"Listo! Tu agente de *{tipo}* ya esta configurado.\n\n"
            f"Ahora escribeme como si fueras un cliente y mira como responde. Pruebalo!"
        )
        _add_msg("assistant", respuesta)
        return respuesta

    return "Algo salio mal. Escribeme de nuevo para empezar."


# ════════════════════════════════════════════════════════════
# Onboarding generico — preguntas para tenants normales
# ════════════════════════════════════════════════════════════

async def _handle_onboarding(
    session, conv: Conversation, config: TenantConfig,
    mensaje_usuario: str, tenant_id: uuid.UUID,
) -> str:
    """
    Maneja el flujo de onboarding pregunta por pregunta.
    Retorna el mensaje que se debe enviar al contacto.
    """
    preguntas = config.onboarding_questions or []
    paso = conv.onboarding_step
    contexto = dict(conv.contact_context or {})

    if paso == 0:
        session.add(Message(
            tenant_id=tenant_id, conversation_id=conv.id,
            role="user", content=mensaje_usuario,
        ))
        saludo = (
            f"Hola! Soy {config.agent_name} de {config.business_name}.\n\n"
            f"Antes de ayudarte, necesito hacerte unas preguntas rapidas."
        )
        primera_pregunta = f"{saludo}\n\n*1/{len(preguntas)}* {preguntas[0]}"
        session.add(Message(
            tenant_id=tenant_id, conversation_id=conv.id,
            role="assistant", content=primera_pregunta,
        ))
        conv.onboarding_step = 1
        return primera_pregunta

    pregunta_anterior = preguntas[paso - 1]
    contexto[pregunta_anterior] = mensaje_usuario
    conv.contact_context = contexto

    session.add(Message(
        tenant_id=tenant_id, conversation_id=conv.id,
        role="user", content=mensaje_usuario,
    ))

    if paso < len(preguntas):
        siguiente = f"*{paso + 1}/{len(preguntas)}* {preguntas[paso]}"
        session.add(Message(
            tenant_id=tenant_id, conversation_id=conv.id,
            role="assistant", content=siguiente,
        ))
        conv.onboarding_step = paso + 1
        return siguiente

    conv.onboarding_complete = True
    cierre = "Perfecto, ya tengo toda la informacion. En que puedo ayudarte?"
    session.add(Message(
        tenant_id=tenant_id, conversation_id=conv.id,
        role="assistant", content=cierre,
    ))
    return cierre


# ════════════════════════════════════════════════════════════
# App FastAPI
# ════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _seed_demo_tenant()
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
app.include_router(bookings_router, prefix="/api")
app.include_router(numbers_router, prefix="/api")


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

                # ── Onboarding: preguntas iniciales (si el tenant las tiene) ──
                preguntas = config.onboarding_questions or []
                if preguntas and not conv.onboarding_complete:
                    respuesta = await _handle_onboarding(
                        session, conv, config, msg.texto, tenant_id
                    )
                    conv.last_message_at = datetime.utcnow()
                    await session.commit()
                    await proveedor.enviar_mensaje(msg.telefono, respuesta)
                    logger.info(f"[{tenant_id}] Onboarding paso {conv.onboarding_step} a {msg.telefono}")
                    continue

                # ── Flujo normal con IA ──

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
                # Detectar si tiene recursos (activa booking tools)
                from agent.models import Resource
                res_check = await session.execute(
                    select(Resource).where(Resource.tenant_id == tenant_id, Resource.is_active == True).limit(1)
                )
                has_resources = res_check.scalar_one_or_none() is not None

                resultado = await generar_respuesta(
                    mensaje=msg.texto,
                    historial=historial,
                    system_prompt=config.system_prompt,
                    ai_api_key=config.ai_api_key_encrypted or os.getenv("PLATFORM_OPENAI_KEY", ""),
                    ai_model=config.ai_model,
                    fallback_message=config.fallback_message,
                    error_message=config.error_message,
                    custom_tools=config.custom_tools,
                    contact_context=conv.contact_context or {},
                    tenant_id=tenant_id,
                    enable_bookings=has_resources,
                    niche=config.niche,
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
