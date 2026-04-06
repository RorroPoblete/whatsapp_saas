# agent/providers/__init__.py — Factory de proveedores multi-tenant

from agent.providers.base import ProveedorWhatsApp, MensajeEntrante


def obtener_proveedor(provider: str, credentials: dict) -> ProveedorWhatsApp:
    """Retorna el proveedor de WhatsApp instanciado con credenciales del tenant."""
    if provider == "whapi":
        from agent.providers.whapi import ProveedorWhapi
        return ProveedorWhapi(token=credentials.get("token", ""))
    elif provider == "meta":
        from agent.providers.meta import ProveedorMeta
        return ProveedorMeta(
            access_token=credentials.get("access_token", ""),
            phone_number_id=credentials.get("phone_number_id", ""),
            verify_token=credentials.get("verify_token", "agentkit-verify"),
        )
    elif provider == "twilio":
        from agent.providers.twilio import ProveedorTwilio
        return ProveedorTwilio(
            account_sid=credentials.get("account_sid", ""),
            auth_token=credentials.get("auth_token", ""),
            phone_number=credentials.get("phone_number", ""),
        )
    else:
        raise ValueError(f"Proveedor no soportado: {provider}. Usa: whapi, meta o twilio")
