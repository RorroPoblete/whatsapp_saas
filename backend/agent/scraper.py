# agent/scraper.py — Escanea URLs de negocios y extrae info con IA
from __future__ import annotations

import re
import json
import logging
import httpx
from openai import AsyncOpenAI

logger = logging.getLogger("agentkit")


def extraer_url(texto: str) -> str | None:
    """Extrae una URL del mensaje del usuario."""
    match = re.search(r'https?://[^\s]+', texto)
    if match:
        return match.group(0).rstrip(".,;:!?)")
    match = re.search(r'(?:www\.)?[\w.-]+\.\w{2,}(?:/[^\s]*)?', texto)
    if match:
        return f"https://{match.group(0)}"
    return None


def _extraer_contacto_html(html: str) -> str:
    """Extrae telefonos, emails y direcciones directo del HTML crudo."""
    datos = set()

    # href="tel:..." y href="mailto:..."
    for m in re.finditer(r'href=["\']tel:([^"\']+)["\']', html):
        datos.add(f"Telefono: {m.group(1).strip()}")
    for m in re.finditer(r'href=["\']mailto:([^"\']+)["\']', html):
        datos.add(f"Email: {m.group(1).strip()}")

    # Emails en texto
    for m in re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html):
        datos.add(f"Email: {m}")

    # Telefonos con +
    for m in re.findall(r'\+\d[\d\s\-]{7,}', html):
        datos.add(f"Telefono: {m.strip()}")

    # Redes sociales
    for m in re.finditer(r'href=["\']https?://(?:www\.)?(?:facebook|instagram|twitter|tiktok|linkedin)\.com/[^"\']+["\']', html):
        url_red = m.group().replace("href=", "").strip('"').strip("'")
        datos.add(f"Red social: {url_red}")

    return "\n".join(sorted(datos))


async def fetch_url_text(url: str) -> str:
    """Descarga una URL y extrae TODO el texto posible del HTML."""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20,
        verify=False,
    ) as client:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
        })
        response.raise_for_status()
        html = response.text

    partes = []

    # 1. Contacto extraido del HTML crudo (SIEMPRE se incluye, nunca se trunca)
    contacto = _extraer_contacto_html(html)
    if contacto:
        partes.append(f"CONTACTO:\n{contacto}")

    # 2. Texto visible completo (la fuente principal)
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<(?:br|hr|/p|/div|/li|/h\d)[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text).strip()
    partes.append(f"CONTENIDO:\n{text[:5000]}")

    # 3. Meta tags (compacto)
    metas = []
    title = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
    if title:
        metas.append(f"title: {title.group(1).strip()}")
    for m in re.finditer(
        r'<meta[^>]*(?:name|property)=["\']([^"\']+)["\'][^>]*content=["\']([^"\']*)["\']', html
    ):
        n = m.group(1).lower()
        if any(k in n for k in ("description", "og:title", "og:description")):
            metas.append(f"{m.group(1)}: {m.group(2)}")
    if metas:
        partes.append("META:\n" + "\n".join(metas))

    # 4. JSON-LD (si hay espacio)
    for bloque in re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL
    ):
        try:
            partes.append("SCHEMA:\n" + json.dumps(json.loads(bloque.strip()), ensure_ascii=False)[:1500])
        except json.JSONDecodeError:
            pass

    return "\n\n".join(partes)[:8000]


async def extraer_info_negocio(texto_web: str, api_key: str) -> dict:
    """Usa IA para extraer informacion estructurada del negocio."""
    client = AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": """Eres un experto extrayendo informacion de negocios desde sitios web.
Te voy a dar el contenido completo de un sitio web. Extrae TODA la informacion util.

Responde SOLO con un JSON valido (sin markdown, sin ```), con estos campos:
{
  "nombre": "nombre del negocio",
  "descripcion": "que hace el negocio (2-3 oraciones)",
  "servicios": "todos los productos o servicios (se detallado)",
  "precios": "todos los precios que encuentres, o 'No disponible'",
  "horario": "horario de atencion, o 'No disponible'",
  "contacto": "TODOS los telefonos, emails, direccion fisica, redes sociales",
  "tono_sugerido": "profesional, amigable, vendedor o empatico",
  "info_extra": "cualquier otro dato relevante (politicas, envios, ubicacion, etc.)"
}

Se exhaustivo. Extrae todo lo que sirva para que un agente de WhatsApp responda preguntas sobre este negocio."""},
            {"role": "user", "content": texto_web}
        ],
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


def formatear_resumen(info: dict) -> str:
    """Formatea la info del negocio para presentarla al usuario."""
    lineas = [
        f"*Negocio:* {info.get('nombre', '—')}",
        f"*Descripcion:* {info.get('descripcion', '—')}",
        f"*Servicios:* {info.get('servicios', '—')}",
        f"*Precios:* {info.get('precios', '—')}",
        f"*Horario:* {info.get('horario', '—')}",
        f"*Contacto:* {info.get('contacto', '—')}",
        f"*Tono:* {info.get('tono_sugerido', '—')}",
    ]
    extra = info.get("info_extra")
    if extra and extra != "No disponible":
        lineas.append(f"*Extra:* {extra}")
    return "\n".join(lineas)
