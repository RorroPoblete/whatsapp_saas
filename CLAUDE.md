# AgentKit SaaS — Instrucciones para Claude Code

> Proyecto: Plataforma SaaS multi-tenant para agentes de WhatsApp con IA.
> Este archivo describe la arquitectura y convenciones del proyecto.

---

## 1. Identidad del proyecto

AgentKit es una **plataforma SaaS** donde los usuarios se registran desde un sitio web,
configuran su negocio en un wizard visual, conectan WhatsApp, y su agente de IA
empieza a responder mensajes automaticamente.

**Arquitectura:** Monorepo con `backend/` (FastAPI) y `frontend/` (Next.js 14).

---

## 2. Stack tecnico

| Componente | Tecnologia |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy async + PostgreSQL |
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| IA | OpenAI GPT-4o mini (configurable por tenant) |
| WhatsApp | Whapi.cloud / Meta Cloud API / Twilio |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Migraciones | Alembic |
| Deploy | Railway (backend) + Vercel (frontend) |

---

## 3. Estructura del proyecto

```
whatsapp-agentkit/
├── backend/
│   ├── agent/
│   │   ├── main.py              ← FastAPI app: API REST + webhook multi-tenant
│   │   ├── models.py            ← 7 tablas SQLAlchemy (Tenant, User, TenantConfig, etc.)
│   │   ├── database.py          ← Engine async + session factory
│   │   ├── brain.py             ← Genera respuestas IA (sin globals, recibe config)
│   │   ├── api/
│   │   │   ├── auth.py          ← POST /auth/register, /login, /me
│   │   │   ├── config.py        ← CRUD config + wizard + generate-prompt
│   │   │   ├── conversations.py ← Listar, ver detalle, toggle-ai, archivar
│   │   │   └── analytics.py     ← Metricas y uso diario
│   │   ├── middleware/
│   │   │   └── auth.py          ← JWT validation + get_current_user + get_tenant_id
│   │   ├── providers/
│   │   │   ├── base.py          ← Clase abstracta ProveedorWhatsApp
│   │   │   ├── __init__.py      ← Factory: obtener_proveedor(provider, credentials)
│   │   │   ├── whapi.py         ← Adaptador Whapi.cloud
│   │   │   ├── meta.py          ← Adaptador Meta Cloud API
│   │   │   └── twilio.py        ← Adaptador Twilio
│   │   └── integrations/        ← (futuro) APIs externas configurables
│   ├── alembic/                 ← Migraciones de DB
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── (marketing)/page.tsx ← Landing page con hero, features, pricing
│   │   ├── (auth)/login,register
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx       ← Sidebar + auth guard
│   │   │   ├── dashboard/       ← Cards de metricas, CTA si no ha hecho setup
│   │   │   ├── setup/           ← Wizard 7 pasos (negocio, agente, horario, knowledge, whatsapp, ai, activar)
│   │   │   ├── conversations/   ← Lista + detalle con burbujas estilo WhatsApp
│   │   │   ├── analytics/       ← Graficos de uso
│   │   │   └── settings/        ← Editor de prompt, knowledge base, config
│   ├── components/ui/           ← Button, Input, Card, Badge, StatCard, EmptyState, Toast
│   ├── lib/
│   │   ├── api.ts               ← Cliente HTTP tipado para todo el backend
│   │   └── auth.ts              ← Token management (localStorage)
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           ← backend + frontend + postgres
└── README.md
```

---

## 4. Conceptos clave

### Multi-tenancy
- Cada negocio es un **Tenant** con su propia config, conversaciones y uso.
- Todas las tablas tienen `tenant_id`. No hay datos compartidos entre tenants.
- El webhook es por tenant: `POST /webhook/{tenant_id}`
- Cada tenant configura sus propias credenciales de WhatsApp y API key de IA.

### Flujo de registro
1. Usuario se registra → se crea Tenant + User (owner) + TenantConfig vacia
2. Redirect a `/setup` (wizard de 7 pasos)
3. Al completar el wizard → se genera el system prompt automaticamente
4. El agente se activa y empieza a responder mensajes

### Flujo de un mensaje WhatsApp
1. `POST /webhook/{tenant_id}` recibe payload del proveedor
2. Se carga la config del tenant (con cache en memoria)
3. Se obtiene o crea la conversacion para ese telefono
4. Se genera respuesta con OpenAI (system prompt + historial)
5. Se guardan mensajes + se actualiza usage tracking
6. Se envia respuesta por WhatsApp

---

## 5. Convenciones de codigo

- **Python:** `from __future__ import annotations` en archivos con type hints de Python 3.10+
- **Pydantic models:** usar `Optional[str]` (no `str | None`) por compatibilidad con Python 3.9
- **SQLAlchemy models:** usar `Mapped[Optional[str]]` con `from __future__ import annotations`
- **Frontend:** TypeScript, componentes funcionales, hooks
- **API:** todos los endpoints bajo `/api/`, autenticados con JWT Bearer
- **Nombres:** variables y comentarios en espanol cuando sea descriptivo

---

## 6. Comandos utiles

```bash
# Backend
cd backend
uvicorn agent.main:app --reload --port 8000
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "descripcion"

# Frontend
cd frontend
npm run dev
npm run build

# Docker
docker compose up --build
```

---

## 7. Variables de entorno (backend/.env)

```env
DATABASE_URL=postgresql+asyncpg://agentkit:agentkit@localhost:5432/agentkit
JWT_SECRET=dev-secret-change-in-production
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

Nota: Las API keys de WhatsApp e IA se guardan en la tabla `tenant_configs` por tenant,
NO en variables de entorno del servidor.
