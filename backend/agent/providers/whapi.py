# agent/providers/whapi.py — Adaptador Whapi.cloud (multi-tenant)

import logging
import httpx
from fastapi import Request
from agent.providers.base import ProveedorWhatsApp, MensajeEntrante

logger = logging.getLogger("agentkit")


class ProveedorWhapi(ProveedorWhatsApp):
    """Proveedor de WhatsApp usando Whapi.cloud."""

    def __init__(self, token: str):
        self.token = token
        self.url_envio = "https://gate.whapi.cloud/messages/text"

    @staticmethod
    def _limpiar_telefono(chat_id: str) -> str:
        """Convierte '56971374935@s.whatsapp.net' → '+56971374935'."""
        numero = chat_id.split("@")[0]
        if numero and not numero.startswith("+"):
            numero = f"+{numero}"
        return numero

    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        body = await request.json()
        mensajes = []
        for msg in body.get("messages", []):
            chat_id = msg.get("chat_id", "")
            mensajes.append(MensajeEntrante(
                telefono=self._limpiar_telefono(chat_id),
                texto=msg.get("text", {}).get("body", ""),
                mensaje_id=msg.get("id", ""),
                es_propio=msg.get("from_me", False),
            ))
        return mensajes

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        if not self.token:
            logger.warning("WHAPI_TOKEN no configurado — mensaje no enviado")
            return False
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.url_envio,
                json={"to": telefono, "body": mensaje},
                headers=headers,
            )
            if r.status_code != 200:
                logger.error(f"Error Whapi: {r.status_code} — {r.text}")
            return r.status_code == 200
