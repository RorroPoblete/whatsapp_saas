# agent/brain.py — Cerebro del agente: multi-tenant, provider-agnostic
from __future__ import annotations

"""
Genera respuestas IA usando la configuracion del tenant.
Soporta OpenAI (default) con tool calling.
Sin globals — todo se recibe por parametro.
"""

import json
import logging
from datetime import datetime
from openai import AsyncOpenAI

logger = logging.getLogger("agentkit")


# Herramientas built-in disponibles para todos los tenants
BUILTIN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "registrar_lead",
            "description": "Registra un cliente interesado para seguimiento. Usala cuando tengas nombre, telefono e interes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "telefono": {"type": "string", "description": "Telefono del cliente"},
                    "nombre": {"type": "string", "description": "Nombre completo"},
                    "interes": {"type": "string", "description": "Servicio o producto de interes"},
                },
                "required": ["telefono", "nombre", "interes"],
            },
        },
    },
]


def _ejecutar_herramienta_builtin(nombre: str, parametros: dict) -> str:
    """Ejecuta herramientas built-in que no requieren config externa."""
    if nombre == "registrar_lead":
        logger.info(f"Lead registrado: {parametros}")
        return json.dumps({
            "status": "registrado",
            **parametros,
            "fecha": datetime.now().isoformat(),
        }, ensure_ascii=False)

    return json.dumps({"error": f"Herramienta '{nombre}' no encontrada"})


async def generar_respuesta(
    mensaje: str,
    historial: list[dict],
    system_prompt: str,
    ai_api_key: str,
    ai_model: str = "gpt-4o-mini",
    fallback_message: str = "Disculpa, no entendi tu mensaje.",
    error_message: str = "Lo siento, problemas tecnicos. Intenta de nuevo.",
    custom_tools: list | None = None,
) -> dict:
    """
    Genera una respuesta usando la API de IA configurada por el tenant.

    Returns:
        dict con "respuesta" (str), "tokens_input" (int), "tokens_output" (int)
    """
    if not mensaje or len(mensaje.strip()) < 2:
        return {"respuesta": fallback_message, "tokens_input": 0, "tokens_output": 0}

    # Inyectar fecha actual en el prompt
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_prompt = f"{system_prompt}\n\n## Contexto temporal\nFecha y hora actual: {fecha_actual}"

    # Construir mensajes
    mensajes = [{"role": "system", "content": full_prompt}]
    for msg in historial:
        mensajes.append({"role": msg["role"], "content": msg["content"]})
    mensajes.append({"role": "user", "content": mensaje})

    # Herramientas: built-in + custom del tenant
    tools = BUILTIN_TOOLS.copy()
    if custom_tools:
        tools.extend(custom_tools)

    client = AsyncOpenAI(api_key=ai_api_key)

    total_input = 0
    total_output = 0

    try:
        while True:
            response = await client.chat.completions.create(
                model=ai_model,
                max_tokens=512,
                messages=mensajes,
                tools=tools if tools else None,
            )

            choice = response.choices[0]
            usage = response.usage
            total_input += usage.prompt_tokens
            total_output += usage.completion_tokens

            logger.info(f"IA ({ai_model}) {usage.prompt_tokens}in/{usage.completion_tokens}out stop:{choice.finish_reason}")

            if choice.finish_reason == "stop":
                texto = choice.message.content or ""
                return {
                    "respuesta": texto if texto else fallback_message,
                    "tokens_input": total_input,
                    "tokens_output": total_output,
                }

            if choice.finish_reason == "tool_calls":
                mensajes.append(choice.message)

                for tool_call in choice.message.tool_calls:
                    parametros = json.loads(tool_call.function.arguments)
                    resultado = _ejecutar_herramienta_builtin(
                        tool_call.function.name, parametros
                    )
                    mensajes.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": resultado,
                    })
                continue

            break

        return {"respuesta": error_message, "tokens_input": total_input, "tokens_output": total_output}

    except Exception as e:
        logger.error(f"Error IA API: {e}")
        return {"respuesta": error_message, "tokens_input": total_input, "tokens_output": total_output}
