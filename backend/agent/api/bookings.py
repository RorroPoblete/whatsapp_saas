# agent/api/bookings.py — CRUD de servicios, recursos y reservas
from __future__ import annotations

import uuid
import json
import re
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent.database import get_db
from agent.models import Service, Resource, Booking, BookingStatus, TenantConfig
from agent.middleware.auth import get_current_tenant_id

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ── Schemas ───────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name: str
    niche: str = "custom"  # restaurant, hotel, agenda, custom
    description: str = ""


class ServiceResponse(BaseModel):
    id: str
    name: str
    niche: str
    description: str
    is_active: bool
    resource_count: int


class ResourceCreate(BaseModel):
    service_id: str
    name: str
    resource_type: str = "custom"
    capacity: int = 1
    duration_minutes: int = 60
    description: str = ""


class ResourceResponse(BaseModel):
    id: str
    service_id: str
    service_name: str
    name: str
    resource_type: str
    capacity: int
    duration_minutes: int
    description: str
    is_active: bool


class BookingResponse(BaseModel):
    id: str
    resource_name: str
    resource_type: str
    service_name: str
    contact_phone: str
    contact_name: str
    date: str
    time_start: str
    time_end: str
    guests: int
    status: str
    notes: str
    created_at: str


class BookingCreate(BaseModel):
    resource_id: str
    contact_phone: str
    contact_name: str = ""
    date: str
    time_start: str
    time_end: str = ""
    guests: int = 1
    notes: str = ""


class AvailabilityQuery(BaseModel):
    date: str
    time_start: str = ""
    guests: int = 1


# ── Servicios ─────────────────────────────────────────────

@router.get("/services", response_model=List[ServiceResponse])
async def list_services(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Service).where(Service.tenant_id == tenant_id).order_by(Service.created_at)
    )
    services = result.scalars().all()
    responses = []
    for s in services:
        res_count = await db.execute(
            select(Resource).where(Resource.service_id == s.id)
        )
        count = len(res_count.scalars().all())
        responses.append(ServiceResponse(
            id=str(s.id), name=s.name, niche=s.niche,
            description=s.description, is_active=s.is_active,
            resource_count=count,
        ))
    return responses


@router.post("/services", response_model=ServiceResponse)
async def create_service(
    body: ServiceCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = Service(
        tenant_id=tenant_id, name=body.name,
        niche=body.niche, description=body.description,
    )
    db.add(service)
    await db.commit()
    return ServiceResponse(
        id=str(service.id), name=service.name, niche=service.niche,
        description=service.description, is_active=service.is_active,
        resource_count=0,
    )


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.tenant_id == tenant_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    await db.delete(service)
    await db.commit()
    return {"status": "ok"}


# ── Recursos ──────────────────────────────────────────────

@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    service_id: Optional[str] = None,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Resource, Service.name)
        .join(Service, Resource.service_id == Service.id)
        .where(Resource.tenant_id == tenant_id)
    )
    if service_id:
        query = query.where(Resource.service_id == uuid.UUID(service_id))
    query = query.order_by(Service.name, Resource.name)

    result = await db.execute(query)
    return [
        ResourceResponse(
            id=str(r.id), service_id=str(r.service_id), service_name=sname,
            name=r.name, resource_type=r.resource_type.value,
            capacity=r.capacity, duration_minutes=r.duration_minutes,
            description=r.description, is_active=r.is_active,
        )
        for r, sname in result.all()
    ]


@router.post("/resources", response_model=ResourceResponse)
async def create_resource(
    body: ResourceCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    # Verificar que el servicio existe
    svc = await db.execute(
        select(Service).where(Service.id == uuid.UUID(body.service_id), Service.tenant_id == tenant_id)
    )
    service = svc.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    resource = Resource(
        tenant_id=tenant_id, service_id=service.id,
        name=body.name, resource_type=body.resource_type,
        capacity=body.capacity, duration_minutes=body.duration_minutes,
        description=body.description,
    )
    db.add(resource)
    await db.commit()
    return ResourceResponse(
        id=str(resource.id), service_id=str(resource.service_id), service_name=service.name,
        name=resource.name, resource_type=resource.resource_type.value,
        capacity=resource.capacity, duration_minutes=resource.duration_minutes,
        description=resource.description, is_active=resource.is_active,
    )


@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.tenant_id == tenant_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    await db.delete(resource)
    await db.commit()
    return {"status": "ok"}


# ── Reservas ──────────────────────────────────────────────

@router.get("", response_model=List[BookingResponse])
async def list_bookings(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Booking, Resource.name, Resource.resource_type, Service.name)
        .join(Resource, Booking.resource_id == Resource.id)
        .join(Service, Resource.service_id == Service.id)
        .where(Booking.tenant_id == tenant_id)
    )
    if date_from:
        query = query.where(Booking.date >= date.fromisoformat(date_from))
    if date_to:
        query = query.where(Booking.date <= date.fromisoformat(date_to))
    if status:
        query = query.where(Booking.status == status)
    query = query.order_by(Booking.date, Booking.time_start)

    result = await db.execute(query)
    return [
        BookingResponse(
            id=str(b.id), resource_name=rname, resource_type=rtype.value,
            service_name=sname,
            contact_phone=b.contact_phone, contact_name=b.contact_name,
            date=str(b.date), time_start=b.time_start, time_end=b.time_end,
            guests=b.guests, status=b.status.value, notes=b.notes,
            created_at=b.created_at.isoformat(),
        )
        for b, rname, rtype, sname in result.all()
    ]


@router.post("", response_model=BookingResponse)
async def create_booking(
    body: BookingCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Resource, Service.name)
        .join(Service, Resource.service_id == Service.id)
        .where(Resource.id == uuid.UUID(body.resource_id), Resource.tenant_id == tenant_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    resource, sname = row

    time_end = body.time_end
    if not time_end:
        h, m = map(int, body.time_start.split(":"))
        total = h * 60 + m + resource.duration_minutes
        time_end = f"{total // 60:02d}:{total % 60:02d}"

    booking_date = date.fromisoformat(body.date)
    conflicts = await db.execute(
        select(Booking).where(
            Booking.resource_id == resource.id,
            Booking.date == booking_date,
            Booking.status.in_(["confirmed", "pending"]),
            Booking.time_start < time_end,
            Booking.time_end > body.time_start,
        )
    )
    if conflicts.scalars().first():
        raise HTTPException(status_code=409, detail="Recurso no disponible en ese horario")

    booking = Booking(
        tenant_id=tenant_id, resource_id=resource.id,
        contact_phone=body.contact_phone, contact_name=body.contact_name,
        date=booking_date, time_start=body.time_start, time_end=time_end,
        guests=body.guests, notes=body.notes,
    )
    db.add(booking)
    await db.commit()
    return BookingResponse(
        id=str(booking.id), resource_name=resource.name,
        resource_type=resource.resource_type.value, service_name=sname,
        contact_phone=booking.contact_phone, contact_name=booking.contact_name,
        date=str(booking.date), time_start=booking.time_start, time_end=booking.time_end,
        guests=booking.guests, status=booking.status.value, notes=booking.notes,
        created_at=booking.created_at.isoformat(),
    )


@router.patch("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.tenant_id == tenant_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    booking.status = BookingStatus.cancelled
    await db.commit()
    return {"status": "cancelled"}


# ── Disponibilidad ────────────────────────────────────────

@router.post("/availability")
async def check_availability(
    body: AvailabilityQuery,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    booking_date = date.fromisoformat(body.date)
    res = await db.execute(
        select(Resource, Service.name)
        .join(Service, Resource.service_id == Service.id)
        .where(Resource.tenant_id == tenant_id, Resource.is_active == True, Resource.capacity >= body.guests)
    )
    all_resources = res.all()

    bookings_res = await db.execute(
        select(Booking).where(
            Booking.tenant_id == tenant_id, Booking.date == booking_date,
            Booking.status.in_(["confirmed", "pending"]),
        )
    )
    bookings = bookings_res.scalars().all()

    available = []
    for resource, sname in all_resources:
        resource_bookings = [b for b in bookings if b.resource_id == resource.id]
        if body.time_start:
            h, m = map(int, body.time_start.split(":"))
            total = h * 60 + m + resource.duration_minutes
            time_end = f"{total // 60:02d}:{total % 60:02d}"
            conflict = any(b.time_start < time_end and b.time_end > body.time_start for b in resource_bookings)
            if not conflict:
                available.append({"id": str(resource.id), "name": resource.name, "service": sname, "capacity": resource.capacity, "time_start": body.time_start, "time_end": time_end})
        else:
            available.append({"id": str(resource.id), "name": resource.name, "service": sname, "capacity": resource.capacity, "bookings_count": len(resource_bookings)})

    return {"date": body.date, "available": available}


# ── Auto-deteccion de servicios ───────────────────────────

@router.post("/detect-services")
async def detect_services(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    from openai import AsyncOpenAI

    result = await db.execute(select(TenantConfig).where(TenantConfig.tenant_id == tenant_id))
    config = result.scalar_one_or_none()
    import os
    if not config or not config.system_prompt:
        raise HTTPException(status_code=400, detail="Configura el system prompt primero")
    api_key = config.ai_api_key_encrypted or os.getenv("PLATFORM_OPENAI_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key de IA no disponible")

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini", max_tokens=1000,
        messages=[
            {"role": "system", "content": """Analiza el system prompt y detecta los servicios reservables del negocio.

Responde SOLO con JSON valido (sin markdown):
{"services": [{"niche": "restaurant|hotel|agenda|custom", "label": "nombre del servicio", "resources": [{"name": "nombre", "type": "table|room|slot|custom", "capacity": 2, "duration_minutes": 90, "description": "desc"}]}]}

Reglas:
- Restaurant: mesas variadas (2-6 pers), 90 min
- Hotel: habitaciones segun tipos mencionados, 1440 min
- Agenda: slots de hora, 30-60 min
- Si hay multiples servicios (hotel+restaurant+eventos), incluye TODOS como servicios separados
- Si no hay servicios reservables: {"services": []}"""},
            {"role": "user", "content": config.system_prompt}
        ],
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


@router.post("/apply-services")
async def apply_services(
    body: dict,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    services = body.get("services", [])
    created = []
    for svc_data in services:
        service = Service(
            tenant_id=tenant_id, name=svc_data.get("label", "Servicio"),
            niche=svc_data.get("niche", "custom"),
        )
        db.add(service)
        await db.flush()
        for r in svc_data.get("resources", []):
            resource = Resource(
                tenant_id=tenant_id, service_id=service.id,
                name=r["name"], resource_type=r.get("type", "custom"),
                capacity=r.get("capacity", 1), duration_minutes=r.get("duration_minutes", 60),
                description=r.get("description", ""),
            )
            db.add(resource)
            created.append(f"{service.name} → {r['name']}")
    await db.commit()
    return {"status": "ok", "created": created, "count": len(created)}
