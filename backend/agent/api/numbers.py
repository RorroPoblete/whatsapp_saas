# agent/api/numbers.py — Pool de numeros WhatsApp (admin)
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent.database import get_db
from agent.models import WhatsAppNumber, TenantConfig
from agent.middleware.auth import get_current_tenant_id

router = APIRouter(prefix="/numbers", tags=["numbers"])


class NumberCreate(BaseModel):
    phone_number: str
    label: str = ""
    provider: str = "whapi"
    credentials: dict = {}


class NumberResponse(BaseModel):
    id: str
    phone_number: str
    label: str
    provider: str
    tenant_id: Optional[str]
    assigned_at: Optional[str]
    is_active: bool


# ── Admin: agregar numeros al pool ────────────────────────

@router.post("", response_model=NumberResponse)
async def add_number(
    body: NumberCreate,
    db: AsyncSession = Depends(get_db),
):
    """Agrega un numero al pool (admin). No requiere tenant."""
    number = WhatsAppNumber(
        phone_number=body.phone_number,
        label=body.label,
        provider=body.provider,
        credentials=body.credentials,
    )
    db.add(number)
    await db.commit()
    return NumberResponse(
        id=str(number.id), phone_number=number.phone_number,
        label=number.label, provider=number.provider,
        tenant_id=None, assigned_at=None, is_active=True,
    )


@router.get("", response_model=List[NumberResponse])
async def list_numbers(db: AsyncSession = Depends(get_db)):
    """Lista todos los numeros del pool (admin)."""
    result = await db.execute(select(WhatsAppNumber).order_by(WhatsAppNumber.created_at))
    return [
        NumberResponse(
            id=str(n.id), phone_number=n.phone_number,
            label=n.label, provider=n.provider,
            tenant_id=str(n.tenant_id) if n.tenant_id else None,
            assigned_at=n.assigned_at.isoformat() if n.assigned_at else None,
            is_active=n.is_active,
        )
        for n in result.scalars().all()
    ]


@router.delete("/{number_id}")
async def delete_number(number_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WhatsAppNumber).where(WhatsAppNumber.id == number_id))
    number = result.scalar_one_or_none()
    if not number:
        raise HTTPException(status_code=404, detail="Numero no encontrado")
    await db.delete(number)
    await db.commit()
    return {"status": "ok"}


# ── Asignar numero a un tenant ────────────────────────────

async def assign_number_to_tenant(tenant_id: uuid.UUID, db: AsyncSession) -> WhatsAppNumber | None:
    """Busca un numero disponible y lo asigna al tenant. Actualiza el tenant config."""
    # Buscar numero libre
    result = await db.execute(
        select(WhatsAppNumber).where(
            WhatsAppNumber.tenant_id.is_(None),
            WhatsAppNumber.is_active == True,
        ).limit(1)
    )
    number = result.scalar_one_or_none()
    if not number:
        return None

    # Asignar al tenant
    number.tenant_id = tenant_id
    number.assigned_at = datetime.utcnow()

    # Actualizar config del tenant con las credenciales del numero
    config_result = await db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = config_result.scalar_one_or_none()
    if config:
        config.whatsapp_provider = number.provider
        config.whatsapp_credentials = number.credentials

    return number


@router.get("/my-number")
async def get_my_number(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el numero asignado al tenant actual."""
    result = await db.execute(
        select(WhatsAppNumber).where(WhatsAppNumber.tenant_id == tenant_id)
    )
    number = result.scalar_one_or_none()
    if not number:
        return {"assigned": False, "phone_number": None}
    return {
        "assigned": True,
        "phone_number": number.phone_number,
        "provider": number.provider,
        "label": number.label,
    }
