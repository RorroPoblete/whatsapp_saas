# agent/booking_tools.py — Herramientas de reservas para el agente IA
from __future__ import annotations

import json
import uuid
import logging
from datetime import date
from sqlalchemy import select
from agent.database import async_session
from agent.models import Resource, Booking, BookingStatus

logger = logging.getLogger("agentkit")


# ── Definiciones de tools para OpenAI ─────────────────────

BOOKING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_disponibilidad",
            "description": "Consulta disponibilidad de mesas, habitaciones o citas para una fecha. Usala cuando el cliente quiera reservar o preguntar si hay disponibilidad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
                    "hora": {"type": "string", "description": "Hora en formato HH:MM (opcional, si el cliente la menciona)"},
                    "personas": {"type": "integer", "description": "Cantidad de personas (default 1)"},
                },
                "required": ["fecha"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_reserva",
            "description": "Crea una reserva confirmada. Usala SOLO cuando tengas: recurso disponible, fecha, hora y nombre del cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_id": {"type": "string", "description": "ID del recurso (mesa, habitacion, slot)"},
                    "fecha": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
                    "hora": {"type": "string", "description": "Hora de inicio en formato HH:MM"},
                    "nombre": {"type": "string", "description": "Nombre del cliente"},
                    "telefono": {"type": "string", "description": "Telefono del cliente"},
                    "personas": {"type": "integer", "description": "Cantidad de personas"},
                    "notas": {"type": "string", "description": "Notas adicionales (opcional)"},
                },
                "required": ["resource_id", "fecha", "hora", "nombre", "telefono"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancelar_reserva",
            "description": "Cancela una reserva existente. Usala cuando el cliente quiera cancelar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "telefono": {"type": "string", "description": "Telefono del cliente para buscar su reserva"},
                    "fecha": {"type": "string", "description": "Fecha de la reserva a cancelar (YYYY-MM-DD)"},
                },
                "required": ["telefono"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ver_reservas",
            "description": "Muestra las reservas de un cliente. Usala cuando pregunten por sus reservas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "telefono": {"type": "string", "description": "Telefono del cliente"},
                },
                "required": ["telefono"],
            },
        },
    },
]


# ── Ejecutores de tools ───────────────────────────────────

async def ejecutar_booking_tool(nombre: str, params: dict, tenant_id: uuid.UUID) -> str:
    """Ejecuta una herramienta de booking y retorna resultado como string."""
    try:
        if nombre == "consultar_disponibilidad":
            return await _consultar_disponibilidad(tenant_id, params)
        elif nombre == "crear_reserva":
            return await _crear_reserva(tenant_id, params)
        elif nombre == "cancelar_reserva":
            return await _cancelar_reserva(tenant_id, params)
        elif nombre == "ver_reservas":
            return await _ver_reservas(tenant_id, params)
        return json.dumps({"error": f"Herramienta '{nombre}' no encontrada"})
    except Exception as e:
        logger.error(f"Error en booking tool {nombre}: {e}")
        return json.dumps({"error": str(e)})


async def _consultar_disponibilidad(tenant_id: uuid.UUID, params: dict) -> str:
    fecha = date.fromisoformat(params["fecha"])
    hora = params.get("hora", "")
    personas = params.get("personas", 1)

    async with async_session() as session:
        # Recursos activos con capacidad
        res = await session.execute(
            select(Resource).where(
                Resource.tenant_id == tenant_id,
                Resource.is_active == True,
                Resource.capacity >= personas,
            )
        )
        resources = res.scalars().all()

        # Reservas del dia
        bookings_res = await session.execute(
            select(Booking).where(
                Booking.tenant_id == tenant_id,
                Booking.date == fecha,
                Booking.status.in_(["confirmed", "pending"]),
            )
        )
        bookings = bookings_res.scalars().all()

        disponibles = []
        for r in resources:
            r_bookings = [b for b in bookings if b.resource_id == r.id]
            if hora:
                h, m = map(int, hora.split(":"))
                total = h * 60 + m + r.duration_minutes
                t_end = f"{total // 60:02d}:{total % 60:02d}"
                conflict = any(b.time_start < t_end and b.time_end > hora for b in r_bookings)
                if not conflict:
                    disponibles.append({
                        "id": str(r.id),
                        "nombre": r.name,
                        "capacidad": r.capacity,
                        "hora": hora,
                        "hora_fin": t_end,
                    })
            else:
                disponibles.append({
                    "id": str(r.id),
                    "nombre": r.name,
                    "capacidad": r.capacity,
                    "reservas_hoy": len(r_bookings),
                })

    if not disponibles:
        return json.dumps({"disponible": False, "mensaje": f"No hay disponibilidad para {personas} persona(s) el {params['fecha']}"}, ensure_ascii=False)

    return json.dumps({"disponible": True, "opciones": disponibles}, ensure_ascii=False)


async def _crear_reserva(tenant_id: uuid.UUID, params: dict) -> str:
    async with async_session() as session:
        res = await session.execute(
            select(Resource).where(Resource.id == uuid.UUID(params["resource_id"]), Resource.tenant_id == tenant_id)
        )
        resource = res.scalar_one_or_none()
        if not resource:
            return json.dumps({"error": "Recurso no encontrado"})

        fecha = date.fromisoformat(params["fecha"])
        hora = params["hora"]
        h, m = map(int, hora.split(":"))
        total = h * 60 + m + resource.duration_minutes
        time_end = f"{total // 60:02d}:{total % 60:02d}"

        # Verificar conflictos
        conflicts = await session.execute(
            select(Booking).where(
                Booking.resource_id == resource.id,
                Booking.date == fecha,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.time_start < time_end,
                Booking.time_end > hora,
            )
        )
        if conflicts.scalars().first():
            return json.dumps({"error": "Ese horario ya esta reservado"}, ensure_ascii=False)

        booking = Booking(
            tenant_id=tenant_id,
            resource_id=resource.id,
            contact_phone=params.get("telefono", ""),
            contact_name=params.get("nombre", ""),
            date=fecha,
            time_start=hora,
            time_end=time_end,
            guests=params.get("personas", 1),
            notes=params.get("notas", ""),
        )
        session.add(booking)
        await session.commit()

        return json.dumps({
            "reserva_creada": True,
            "id": str(booking.id),
            "recurso": resource.name,
            "fecha": str(fecha),
            "hora": f"{hora} - {time_end}",
            "nombre": booking.contact_name,
            "personas": booking.guests,
        }, ensure_ascii=False)


async def _cancelar_reserva(tenant_id: uuid.UUID, params: dict) -> str:
    telefono = params["telefono"]
    fecha_str = params.get("fecha")

    async with async_session() as session:
        query = select(Booking, Resource.name).join(Resource).where(
            Booking.tenant_id == tenant_id,
            Booking.contact_phone == telefono,
            Booking.status.in_(["confirmed", "pending"]),
        )
        if fecha_str:
            query = query.where(Booking.date == date.fromisoformat(fecha_str))
        query = query.order_by(Booking.date.desc())

        result = await session.execute(query)
        row = result.first()
        if not row:
            return json.dumps({"error": "No se encontro una reserva activa para ese telefono"}, ensure_ascii=False)

        booking, resource_name = row
        booking.status = BookingStatus.cancelled
        await session.commit()

        return json.dumps({
            "cancelada": True,
            "recurso": resource_name,
            "fecha": str(booking.date),
            "hora": booking.time_start,
        }, ensure_ascii=False)


async def _ver_reservas(tenant_id: uuid.UUID, params: dict) -> str:
    telefono = params["telefono"]

    async with async_session() as session:
        result = await session.execute(
            select(Booking, Resource.name).join(Resource).where(
                Booking.tenant_id == tenant_id,
                Booking.contact_phone == telefono,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.date >= date.today(),
            ).order_by(Booking.date, Booking.time_start)
        )
        rows = result.all()

        if not rows:
            return json.dumps({"reservas": [], "mensaje": "No tienes reservas activas"}, ensure_ascii=False)

        reservas = []
        for booking, resource_name in rows:
            reservas.append({
                "recurso": resource_name,
                "fecha": str(booking.date),
                "hora": f"{booking.time_start} - {booking.time_end}",
                "personas": booking.guests,
                "estado": booking.status.value,
            })

        return json.dumps({"reservas": reservas}, ensure_ascii=False)
