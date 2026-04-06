#!/bin/bash
# AgentKit — Script de inicio
# El usuario ejecuta: bash start.sh

set -e

echo ""
echo "==========================================================="
echo "   AgentKit — WhatsApp AI Agent Builder"
echo "==========================================================="
echo ""
echo "  Preparando tu entorno para construir tu agente de IA..."
echo ""

# ── Verificar Python ──────────────────────────────────────────
echo "  [1/4] Verificando Python..."

# Buscar un Python >= 3.11 entre los candidatos disponibles
PYTHON_CMD=""
for candidate in python3 python3.13 python3.12 python3.11 /opt/homebrew/bin/python3 /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11; do
    if command -v "$candidate" &> /dev/null; then
        major=$($candidate -c 'import sys; print(sys.version_info.major)' 2>/dev/null) || continue
        minor=$($candidate -c 'import sys; print(sys.version_info.minor)' 2>/dev/null) || continue
        if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_CMD="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "  ERROR: Necesitas Python 3.11 o superior."
    if command -v python3 &> /dev/null; then
        echo "  Version encontrada: $(python3 --version)"
    fi
    echo "  Descarga la ultima version en: https://python.org/downloads"
    echo ""
    echo "  Si ya lo instalaste con Homebrew, agrega al PATH:"
    echo "    export PATH=\"/opt/homebrew/opt/python@3.12/libexec/bin:\$PATH\""
    echo ""
    exit 1
fi
echo "  OK — $($PYTHON_CMD --version) [$PYTHON_CMD]"

# ── Verificar Claude Code ────────────────────────────────────
echo "  [2/4] Verificando Claude Code..."
if ! command -v claude &> /dev/null; then
    echo ""
    echo "  Claude Code no esta instalado."
    echo ""
    echo "  Para instalarlo:"
    echo "    npm install -g @anthropic-ai/claude-code"
    echo ""
    echo "  Si no tienes npm/Node.js:"
    echo "    https://nodejs.org (descarga LTS)"
    echo ""
    echo "  Despues de instalar, ejecuta 'claude' una vez para autenticarte"
    echo "  y luego vuelve a correr: bash start.sh"
    echo ""
    exit 1
fi
echo "  OK — Claude Code instalado"

# ── Crear carpetas base ──────────────────────────────────────
echo "  [3/4] Preparando carpetas..."
mkdir -p knowledge
echo "  OK — Estructura lista"

# ── Listo ─────────────────────────────────────────────────────
echo "  [4/4] Todo verificado"

echo ""
echo "==========================================================="
echo ""
echo "  Todo listo. Ahora abre Claude Code:"
echo ""
echo "    claude"
echo ""
echo "  Y escribe:"
echo ""
echo "    /build-agent"
echo ""
echo "  Claude Code te guiara paso a paso para construir"
echo "  tu agente de WhatsApp personalizado con IA."
echo ""
echo "==========================================================="
echo ""
