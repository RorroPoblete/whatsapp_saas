# AgentKit — WhatsApp AI Agent Platform

Plataforma SaaS para crear agentes de WhatsApp con inteligencia artificial. Los usuarios se registran, configuran su negocio desde un dashboard web, y su agente empieza a funcionar. Sin programar.

---

## Arquitectura

```
whatsapp-agentkit/
├── backend/          ← FastAPI multi-tenant (Python)
│   ├── agent/
│   │   ├── main.py           # Servidor + webhook multi-tenant
│   │   ├── models.py         # 7 tablas SQLAlchemy (tenants, users, configs...)
│   │   ├── database.py       # Engine PostgreSQL async
│   │   ├── brain.py          # IA con OpenAI (multi-tenant, sin globals)
│   │   ├── api/              # REST: auth, config, conversations, analytics
│   │   ├── middleware/       # JWT auth + tenant context
│   │   └── providers/        # WhatsApp: Whapi, Meta, Twilio
│   ├── alembic/              # Migraciones de base de datos
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         ← Next.js 14 (React + Tailwind)
│   ├── app/
│   │   ├── (marketing)/      # Landing page + pricing
│   │   ├── (auth)/           # Login + registro
│   │   └── (dashboard)/      # Dashboard, setup wizard, conversaciones, settings
│   ├── components/ui/        # Button, Input, Card, Badge, Toast, etc.
│   ├── lib/                  # API client + auth helpers
│   └── Dockerfile
├── docker-compose.yml        # Backend + Frontend + PostgreSQL
└── README.md
```

## Flujo de un mensaje

```
Cliente escribe en WhatsApp
    ↓
Proveedor (Whapi / Meta / Twilio)
    ↓  POST /webhook/{tenant_id}
FastAPI identifica el tenant → carga config de DB
    ↓
Obtiene historial de conversacion
    ↓
OpenAI GPT-4o mini genera respuesta (con system prompt del tenant)
    ↓
Guarda mensajes + actualiza usage tracking
    ↓
Envia respuesta por WhatsApp
    ↓
Cliente recibe respuesta
```

## Empezar en desarrollo

### Opcion 1: Docker Compose (recomendado)

```bash
# Levanta backend + frontend + PostgreSQL
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Opcion 2: Manual

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Configura .env (copia de .env.example)
python -m alembic upgrade head
uvicorn agent.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/auth/register` | Registro (crea tenant + user) |
| POST | `/api/auth/login` | Login (retorna JWT) |
| GET | `/api/auth/me` | Perfil del usuario |
| GET | `/api/config` | Config del agente |
| PUT | `/api/config` | Actualizar config |
| PUT | `/api/config/whatsapp` | Configurar WhatsApp |
| PUT | `/api/config/ai` | Configurar API key IA |
| POST | `/api/config/generate-prompt` | Auto-generar system prompt |
| POST | `/api/config/complete-setup` | Activar agente |
| GET | `/api/config/webhook-url` | URL del webhook |
| GET | `/api/conversations` | Listar conversaciones |
| GET | `/api/conversations/{id}` | Detalle + mensajes |
| PATCH | `/api/conversations/{id}/toggle-ai` | Activar/pausar IA |
| GET | `/api/analytics/summary` | Metricas y uso |
| POST | `/webhook/{tenant_id}` | Webhook de WhatsApp |

## Base de datos

7 tablas multi-tenant:

| Tabla | Proposito |
|-------|-----------|
| `tenants` | Negocios registrados (plan, slug, activo) |
| `users` | Usuarios con roles (owner, admin, viewer) |
| `tenant_configs` | Config completa del agente (prompt, credenciales, tools) |
| `conversations` | Conversaciones por telefono por tenant |
| `messages` | Historial con tenant_id |
| `usage_tracking` | Mensajes/tokens por dia por tenant |
| `webhook_logs` | Debug de webhooks |

## Stack

| Componente | Tecnologia |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy async |
| Frontend | Next.js 14 + Tailwind + Lucide icons |
| Base de datos | PostgreSQL (dev: SQLite) |
| IA | OpenAI GPT-4o mini |
| WhatsApp | Whapi.cloud / Meta Cloud API / Twilio |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Migraciones | Alembic |
| Deploy | Railway (backend) + Vercel (frontend) |

## Deploy a produccion

1. **Backend en Railway:**
   - Conectar repo GitHub
   - Root directory: `backend/`
   - Variables de entorno: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `PORT=8000`, `ENVIRONMENT=production`

2. **Frontend en Vercel:**
   - Conectar repo GitHub
   - Root directory: `frontend/`
   - Variable: `NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app`

3. **PostgreSQL:** Railway addon o Supabase

## Licencia

MIT
