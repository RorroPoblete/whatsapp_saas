# AgentKit SaaS — Instrucciones para Claude Code

> Proyecto: Plataforma SaaS multi-tenant para agentes de WhatsApp con IA + sistema de reservas.
> Este archivo describe la arquitectura y convenciones del proyecto.

---

## 1. Identidad del proyecto

AgentKit es una **plataforma SaaS** donde los negocios se registran desde un sitio web,
configuran su agente en un wizard visual, conectan WhatsApp, y su agente de IA
empieza a responder mensajes y gestionar reservas automaticamente.

**Nichos soportados:** restaurantes (mesas), hoteles (habitaciones), agenda (citas), personalizado.

**Arquitectura:** Monorepo con `backend/` (FastAPI) y `frontend/` (Next.js 14).

---

## 2. Stack tecnico

| Componente | Tecnologia |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy async + PostgreSQL |
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| IA | OpenAI GPT-4o mini con tool calling |
| Reservas | Sistema propio con verificacion de conflictos |
| WhatsApp | Whapi.cloud / Meta Cloud API / Twilio |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Migraciones | Alembic |
| Deploy | Railway (backend) + Vercel (frontend) |

---

## 3. Estructura del proyecto

```
whatsapp_saas/
├── backend/
│   ├── agent/
│   │   ├── main.py              ← FastAPI app + webhook + seed hotel demo
│   │   ├── models.py            ← 9 tablas SQLAlchemy (Tenant, User, Resource, Booking, etc.)
│   │   ├── database.py          ← Engine async + session factory
│   │   ├── brain.py             ← Genera respuestas IA con tool calling
│   │   ├── booking_tools.py     ← 4 herramientas IA: disponibilidad, crear/cancelar/ver reservas
│   │   ├── niches.py            ← Templates por nicho (restaurant, hotel, agenda, custom)
│   │   ├── scraper.py           ← Scraping de sitios web (extraer info negocio)
│   │   ├── api/
│   │   │   ├── auth.py          ← POST /auth/register, /login, /me
│   │   │   ├── config.py        ← CRUD config + wizard + generate-prompt
│   │   │   ├── conversations.py ← Listar, ver detalle, toggle-ai, archivar
│   │   │   ├── analytics.py     ← Metricas y uso diario
│   │   │   └── bookings.py      ← CRUD recursos + reservas + disponibilidad
│   │   ├── middleware/
│   │   │   └── auth.py          ← JWT validation + get_current_user + get_tenant_id
│   │   └── providers/
│   │       ├── base.py          ← Clase abstracta ProveedorWhatsApp
│   │       ├── __init__.py      ← Factory: obtener_proveedor(provider, credentials)
│   │       ├── whapi.py         ← Adaptador Whapi.cloud (limpia numeros @s.whatsapp.net)
│   │       ├── meta.py          ← Adaptador Meta Cloud API
│   │       └── twilio.py        ← Adaptador Twilio
│   ├── alembic/                 ← Migraciones de DB
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── (marketing)/page.tsx ← Landing + pricing CLP ($99.990 / $199.990 / $349.990)
│   │   ├── (auth)/login,register
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx       ← Sidebar con 6 secciones + auth guard
│   │   │   ├── dashboard/       ← Cards de metricas
│   │   │   ├── setup/           ← Wizard 8 pasos (incluye onboarding questions)
│   │   │   ├── conversations/   ← Lista + detalle (burbujas WhatsApp, numeros formateados)
│   │   │   ├── resources/       ← CRUD mesas/habitaciones/slots
│   │   │   ├── bookings-view/   ← Lista de reservas con filtros y cancelacion
│   │   │   ├── analytics/       ← Graficos de uso 30 dias
│   │   │   └── settings/        ← Editor de prompt, knowledge base, config
│   ├── lib/
│   │   ├── api.ts               ← Cliente HTTP tipado (incluye booking endpoints)
│   │   └── auth.ts              ← Token management (localStorage)
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           ← backend + frontend + postgres
├── PRICING.md                   ← Modelo de pricing Chile (analisis competencia, costos, planes)
└── README.md
```

---

## 4. Conceptos clave

### Multi-tenancy
- Cada negocio es un **Tenant** con su propia config, conversaciones, recursos y reservas.
- Todas las tablas tienen `tenant_id`. No hay datos compartidos entre tenants.
- El webhook es por tenant: `POST /webhook/{tenant_id}`

### Nichos de negocio
- Cada tenant tiene un `niche`: restaurant, hotel, agenda o custom.
- El nicho determina: tipo de recursos, instrucciones de booking para la IA, y labels en el dashboard.
- Templates en `niches.py` con recursos default por nicho.

### Sistema de reservas
- **Resource:** mesa, habitacion, slot u otro (nombre, tipo, capacidad, duracion).
- **Booking:** reserva vinculada a un recurso, con fecha, hora, estado y contacto.
- La IA puede gestionar reservas via tool calling (consultar, crear, cancelar, ver).
- Verificacion automatica de conflictos de horario.

### Onboarding de contactos
- Los tenants pueden configurar preguntas que el bot hace a contactos nuevos.
- Las respuestas se guardan en `conversation.contact_context` y se inyectan en el prompt.

### Seed demo (Hotel Il Giardino)
- Al iniciar con `DEMO_WHAPI_TOKEN` + `DEMO_OPENAI_KEY`, se crea automaticamente:
  - Tenant con system prompt completo (suites, restaurant, menu, precios, eventos)
  - 4 suites como recursos reservables
  - Usuario admin: `admin@hotelilgiardino.cl` / `ilgiardino2026`
- El bot responde como "Isabella", asistente del hotel.

### Flujo de un mensaje WhatsApp
1. `POST /webhook/{tenant_id}` recibe payload del proveedor
2. Se carga config del tenant (con cache)
3. Se obtiene o crea conversacion (numeros limpios, sin @s.whatsapp.net)
4. Si tiene onboarding questions → flujo de preguntas
5. Si tiene recursos → se activan booking tools para la IA
6. OpenAI genera respuesta (system prompt + historial + contact context + tools)
7. Se guardan mensajes + se actualiza usage tracking
8. Se envia respuesta por WhatsApp

---

## 5. Convenciones de codigo

- **Python:** `from __future__ import annotations` en archivos con type hints de Python 3.10+
- **Pydantic models:** usar `Optional[str]` (no `str | None`) por compatibilidad con Python 3.9
- **SQLAlchemy models:** usar `Mapped[Optional[str]]` con `from __future__ import annotations`
- **Frontend:** TypeScript, componentes funcionales, hooks
- **API:** todos los endpoints bajo `/api/`, autenticados con JWT Bearer
- **Nombres:** variables y comentarios en espanol cuando sea descriptivo
- **Respuestas del bot:** cortas (2-3 oraciones), sin markdown, sin emojis, como una persona real por WhatsApp

---

## 6. Comandos utiles

```bash
# Docker (recomendado)
docker compose up --build              # levantar todo
docker compose down -v                 # borrar todo (incluida DB)
docker compose logs backend --tail=50  # ver logs

# Backend (manual)
cd backend
uvicorn agent.main:app --reload --port 8000
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "descripcion"

# Frontend (manual)
cd frontend
npm run dev
npm run build

# Tunel para webhook local
npx ngrok http 8000
```

---

## 7. Variables de entorno (backend/.env)

```env
DATABASE_URL=postgresql+asyncpg://agentkit:agentkit@localhost:5432/agentkit
JWT_SECRET=dev-secret-change-in-production
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000

# Demo mode (seed Hotel Il Giardino)
DEMO_WHAPI_TOKEN=tu-token-de-whapi
DEMO_OPENAI_KEY=sk-tu-api-key-de-openai
```

Las API keys de WhatsApp e IA por tenant se guardan en la tabla `tenant_configs`, NO en variables de entorno.
