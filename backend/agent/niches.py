# agent/niches.py — Templates de configuracion por nicho de negocio
from __future__ import annotations

NICHE_TEMPLATES = {
    "restaurant": {
        "label": "Restaurante",
        "default_resources": [
            {"name": "Mesa 1", "type": "table", "capacity": 2, "duration": 90},
            {"name": "Mesa 2", "type": "table", "capacity": 2, "duration": 90},
            {"name": "Mesa 3", "type": "table", "capacity": 4, "duration": 90},
            {"name": "Mesa 4", "type": "table", "capacity": 4, "duration": 90},
            {"name": "Mesa 5", "type": "table", "capacity": 6, "duration": 90},
            {"name": "Mesa 6", "type": "table", "capacity": 6, "duration": 90},
        ],
        "resource_label": "Mesas",
        "resource_fields": {"capacity_label": "Personas", "duration_label": "Duracion (min)"},
        "booking_prompt_section": """## Sistema de reservas
Tienes acceso a un sistema de reservas de mesas. Puedes:
- Consultar disponibilidad de mesas para una fecha y hora
- Crear reservas cuando el cliente te de fecha, hora, nombre y cantidad de personas
- Cancelar reservas si el cliente lo pide
- Mostrar las reservas de un cliente

Cuando alguien quiera reservar, pregunta: fecha, hora, cuantas personas y a nombre de quien.
No inventes disponibilidad, siempre usa la herramienta consultar_disponibilidad primero.""",
    },

    "hotel": {
        "label": "Hotel",
        "default_resources": [
            {"name": "Habitacion Standard", "type": "room", "capacity": 2, "duration": 1440},
            {"name": "Habitacion Superior", "type": "room", "capacity": 2, "duration": 1440},
            {"name": "Suite", "type": "room", "capacity": 2, "duration": 1440},
        ],
        "resource_label": "Habitaciones",
        "resource_fields": {"capacity_label": "Huespedes", "duration_label": "Duracion (noches x 1440 min)"},
        "booking_prompt_section": """## Sistema de reservas
Tienes acceso a un sistema de reservas de habitaciones. Puedes:
- Consultar disponibilidad de habitaciones para fechas especificas
- Crear reservas cuando el cliente confirme fechas, tipo de habitacion y nombre
- Cancelar reservas si el cliente lo pide
- Mostrar las reservas de un cliente

Cuando alguien quiera reservar, pregunta: fecha de check-in, cantidad de noches, tipo de habitacion preferida y nombre.
No inventes disponibilidad, siempre usa la herramienta consultar_disponibilidad primero.""",
    },

    "agenda": {
        "label": "Agenda / Citas",
        "default_resources": [
            {"name": "Hora 09:00", "type": "slot", "capacity": 1, "duration": 60},
            {"name": "Hora 10:00", "type": "slot", "capacity": 1, "duration": 60},
            {"name": "Hora 11:00", "type": "slot", "capacity": 1, "duration": 60},
            {"name": "Hora 12:00", "type": "slot", "capacity": 1, "duration": 60},
            {"name": "Hora 15:00", "type": "slot", "capacity": 1, "duration": 60},
            {"name": "Hora 16:00", "type": "slot", "capacity": 1, "duration": 60},
            {"name": "Hora 17:00", "type": "slot", "capacity": 1, "duration": 60},
        ],
        "resource_label": "Horarios disponibles",
        "resource_fields": {"capacity_label": "Personas por slot", "duration_label": "Duracion (min)"},
        "booking_prompt_section": """## Sistema de agenda
Tienes acceso a un sistema de agendamiento de citas. Puedes:
- Consultar horarios disponibles para una fecha
- Agendar citas cuando el cliente elija fecha, hora y de su nombre
- Cancelar citas si el cliente lo pide
- Mostrar las citas de un cliente

Cuando alguien quiera agendar, pregunta: fecha preferida, horario preferido y nombre.
No inventes disponibilidad, siempre usa la herramienta consultar_disponibilidad primero.""",
    },

    "custom": {
        "label": "Personalizado",
        "default_resources": [],
        "resource_label": "Recursos",
        "resource_fields": {"capacity_label": "Capacidad", "duration_label": "Duracion (min)"},
        "booking_prompt_section": """## Sistema de reservas
Tienes acceso a un sistema de reservas. Puedes:
- Consultar disponibilidad para una fecha
- Crear reservas
- Cancelar reservas
- Mostrar reservas de un cliente

Siempre usa la herramienta consultar_disponibilidad antes de confirmar algo.""",
    },
}


def get_niche_template(niche: str) -> dict:
    return NICHE_TEMPLATES.get(niche, NICHE_TEMPLATES["custom"])
