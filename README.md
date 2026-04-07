# AgentKit — Plataforma de Agentes WhatsApp con IA

Plataforma SaaS multi-tenant para crear agentes de WhatsApp con inteligencia artificial. Los negocios se registran, configuran su agente desde un dashboard, y el bot empieza a responder y gestionar reservas automaticamente.

Nichos soportados: restaurantes (mesas), hoteles (habitaciones), agenda (citas) y personalizado.

---

## Arquitectura

```
whatsapp_saas/
├── backend/                ← FastAPI multi-tenant (Python)
│   ├── agent/
│   │   ├── main.py                # Servidor + webhook + seed demo
│   │   ├── models.py              # 9 tablas SQLAlchemy
│   │   ├── database.py            # Engine PostgreSQL async
│   │   ├── brain.py               # IA con OpenAI + tool calling
│   │   ├── booking_tools.py       # Herramientas IA para reservas
│   │   ├── niches.py              # Templates por nicho de negocio
│   │   ├── scraper.py             # Scraping de sitios web
│   │   ├── api/
│   │   │   ├── auth.py            # Registro, login, perfil
│   │   │   ├── config.py          # Config del agente + wizard
│   │   │   ├── conversations.py   # Conversaciones + mensajes
│   │   │   ├── analytics.py       # Metricas de uso
│   │   │   └── bookings.py        # CRUD recursos + reservas
│   │   ├── middleware/auth.py     # JWT + tenant context
│   │   └── providers/             # WhatsApp: Whapi, Meta, Twilio
│   ├── alembic/                   # Migraciones
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               ← Next.js 14 (React + Tailwind)
│   ├── app/
│   │   ├── (marketing)/           # Landing + pricing (CLP)
│   │   ├── (auth)/                # Login + registro
│   │   └── (dashboard)/
│   │       ├── dashboard/         # Metricas principales
│   │       ├── setup/             # Wizard 8 pasos
│   │       ├── conversations/     # Chat estilo WhatsApp
│   │       ├── resources/         # CRUD mesas/habitaciones/slots
│   │       ├── bookings-view/     # Lista de reservas
│   │       ├── analytics/         # Graficos de uso
│   │       └── settings/          # Config del agente
│   ├── lib/
│   │   ├── api.ts                 # Cliente HTTP tipado
│   │   └── auth.ts                # Token management
│   └── Dockerfile
├── docker-compose.yml
├── PRICING.md                     # Modelo de pricing Chile
└── CLAUDE.md                      # Instrucciones del proyecto
```

## Flujo de un mensaje

```
Cliente escribe en WhatsApp
    ↓
Proveedor (Whapi / Meta / Twilio)
    ↓  POST /webhook/{tenant_id}
FastAPI identifica tenant → carga config
    ↓
Onboarding? → preguntas iniciales (si configurado)
    ↓
Carga historial (ultimos 20 mensajes)
    ↓
OpenAI GPT-4o mini genera respuesta
  → Puede llamar tools: consultar_disponibilidad, crear_reserva, etc.
    ↓
Guarda mensajes + actualiza usage tracking
    ↓
Envia respuesta por WhatsApp
```

## Sistema de reservas

El agente gestiona reservas automaticamente segun el nicho del negocio:

| Nicho | Recurso | Ejemplo de conversacion |
|-------|---------|------------------------|
| Restaurant | Mesas (capacidad, duracion) | "Mesa para 4 mananana a las 21:00" |
| Hotel | Habitaciones (tipo, huespedes) | "Suite para el fin de semana" |
| Agenda | Slots de hora (duracion) | "Cita para el martes a las 10:00" |
| Custom | Configurable | Lo que necesites |

La IA tiene 4 herramientas integradas:
- `consultar_disponibilidad` — verifica recursos libres por fecha/hora/capacidad
- `crear_reserva` — confirma reserva con nombre, fecha, hora
- `cancelar_reserva` — cancela por telefono
- `ver_reservas` — muestra reservas activas del cliente

## Empezar en desarrollo

### 1. Configurar variables de entorno

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://agentkit:agentkit@localhost:5432/agentkit
JWT_SECRET=dev-secret-change-in-production
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
DEMO_WHAPI_TOKEN=tu-token-de-whapi
DEMO_OPENAI_KEY=sk-tu-api-key-de-openai
```

### 2. Levantar con Docker Compose

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Seed automatico

Al iniciar, si `DEMO_WHAPI_TOKEN` y `DEMO_OPENAI_KEY` estan configurados, se crea automaticamente:
- Tenant **Hotel Il Giardino** con toda su info (suites, restaurant, menu, precios)
- 4 suites como recursos reservables
- Usuario admin: `admin@hotelilgiardino.cl` / `ilgiardino2026`
- Webhook listo para conectar a Whapi

El webhook URL aparece en los logs:
```
══════════════════════════════════════════════
  HOTEL IL GIARDINO CREADO
  Webhook: /webhook/{uuid}
  Dashboard: admin@hotelilgiardino.cl / ilgiardino2026
══════════════════════════════════════════════
```

### 4. Conectar WhatsApp

Para desarrollo local, usa ngrok:
```bash
npx ngrok http 8000
```
Copia la URL y agregale el path del webhook. Pegala en Whapi.cloud como webhook de mensajes entrantes.

### Opcion manual (sin Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn agent.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

### Auth
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/auth/register` | Registro (crea tenant + user + config) |
| POST | `/api/auth/login` | Login (retorna JWT) |
| GET | `/api/auth/me` | Perfil del usuario |

### Config
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/config` | Config del agente |
| PUT | `/api/config` | Actualizar config |
| PUT | `/api/config/whatsapp` | Configurar proveedor WhatsApp |
| PUT | `/api/config/ai` | Configurar API key IA |
| POST | `/api/config/generate-prompt` | Auto-generar system prompt |
| POST | `/api/config/complete-setup` | Activar agente |
| GET | `/api/config/webhook-url` | URL del webhook |

### Conversaciones
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/conversations` | Listar (filtro, busqueda, paginacion) |
| GET | `/api/conversations/{id}` | Detalle + mensajes |
| PATCH | `/api/conversations/{id}/toggle-ai` | Activar/pausar IA |
| PATCH | `/api/conversations/{id}/archive` | Archivar |

### Reservas
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/bookings/resources` | Listar recursos |
| POST | `/api/bookings/resources` | Crear recurso |
| DELETE | `/api/bookings/resources/{id}` | Eliminar recurso |
| GET | `/api/bookings` | Listar reservas (filtros fecha/estado) |
| POST | `/api/bookings` | Crear reserva |
| PATCH | `/api/bookings/{id}/cancel` | Cancelar reserva |
| POST | `/api/bookings/availability` | Consultar disponibilidad |

### Analytics + Webhook
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/analytics/summary` | Metricas y uso diario |
| POST | `/webhook/{tenant_id}` | Webhook WhatsApp (multi-tenant) |

## Base de datos

9 tablas multi-tenant:

| Tabla | Proposito |
|-------|-----------|
| `tenants` | Negocios registrados (plan, slug) |
| `users` | Usuarios con roles (owner, admin, viewer) |
| `tenant_configs` | Config del agente (prompt, credenciales, nicho, tools) |
| `conversations` | Conversaciones por telefono (onboarding state, contact context) |
| `messages` | Historial de mensajes |
| `resources` | Mesas, habitaciones, slots (tipo, capacidad, duracion) |
| `bookings` | Reservas (recurso, fecha, hora, estado, contacto) |
| `usage_tracking` | Mensajes y tokens por dia |
| `webhook_logs` | Debug de webhooks |

## Stack

| Componente | Tecnologia |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy async + PostgreSQL |
| Frontend | Next.js 14 (App Router) + Tailwind CSS + Lucide |
| IA | OpenAI GPT-4o mini con tool calling |
| Reservas | Sistema propio con verificacion de conflictos |
| WhatsApp | Whapi.cloud / Meta Cloud API / Twilio |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Migraciones | Alembic |
| Deploy | Railway (backend) + Vercel (frontend) |

## Deploy a produccion

1. **Backend en Railway:**
   - Root directory: `backend/`
   - Variables: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `PORT=8000`, `ENVIRONMENT=production`, `DEMO_WHAPI_TOKEN`, `DEMO_OPENAI_KEY`

2. **Frontend en Vercel:**
   - Root directory: `frontend/`
   - Variable: `NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app`

3. **PostgreSQL:** Railway addon o Supabase

4. **Webhook:** Configurar URL publica del backend en Whapi.cloud

## Licencia

MIT



Prueba el flujo nuevo con el usuario vacio:                                           
   
  1. Login con demo@agentkit.cl / demo1234                                              
  2. Te manda al setup automaticamente                            
  3. En el paso 1, escribe algo como:                                                   
                                                                                        
  Somos una barberia en Providencia, Santiago. Tenemos 3 sillones                       
  de corte y 1 de barba. Horario lunes a sabado 10:00 a 20:00.                          
  Servicios: corte clasico $8.000, corte + barba $12.000,                               
  barba sola $6.000, colorimetria desde $15.000. Direccion:                             
  Av. Providencia 1234. Telefono +56 9 1234 5678.                                       
                                                                                        
  4. Click "Generar mi agente" → la IA genera:                                          
    - System prompt completo                                                            
    - Servicio "Barberia" con 4 sillones                                                
    - Agent name, tono, horario, contacto                                               
  5. Edita lo que quieras (prompt, quitar/agregar recursos)                             
  6. Conecta WhatsApp + API key                                                         
  7. Activa                                                                             
                                                                                        
  Tambien podes poner una URL real y que scrapee la web. Las dos fuentes (descripcion + 
  URL) se combinan.       