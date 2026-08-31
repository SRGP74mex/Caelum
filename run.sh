#!/usr/bin/env bash
# ==============================================================================
# CAELUM - SCRIPT DE LANZAMIENTO Y AUTO-CONFIGURACIÓN UNIVERSAL
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Comprobar que Python 3 está disponible en el sistema
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error: Python 3 no está instalado en este sistema."
    if command -v apt >/dev/null 2>&1; then
        echo "   👉 Instálalo ejecutando: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    elif command -v pacman >/dev/null 2>&1; then
        echo "   👉 Instálalo ejecutando: sudo pacman -S python python-pip"
    elif command -v dnf >/dev/null 2>&1; then
        echo "   👉 Instálalo ejecutando: sudo dnf install -y python3 python3-pip"
    fi
    exit 1
fi

# 2. Verificar y auto-crear el entorno virtual si no existe
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "📦 Preparando entorno virtual aislado para Caelum..."
    
    # Intentar crear venv estándar
    if ! python3 -m venv "$SCRIPT_DIR/venv" 2>/dev/null; then
        # Si falló (común en Debian/Ubuntu/Mint cuando falta python3-venv)
        echo "⚠️  No se pudo crear venv con ensurepip. Intentando con --without-pip..."
        if ! python3 -m venv --without-pip "$SCRIPT_DIR/venv" 2>/dev/null; then
            echo "❌ Error: Falta el módulo 'venv' de Python en tu distribución."
            if command -v apt >/dev/null 2>&1; then
                echo "   👉 En Linux Mint / Ubuntu / Debian ejecuta:"
                echo "      sudo apt update && sudo apt install -y python3-venv python3-pip libxcb-cursor0"
            elif command -v pacman >/dev/null 2>&1; then
                echo "   👉 En Manjaro / Arch Linux ejecuta:"
                echo "      sudo pacman -S python python-pip"
            fi
            exit 1
        fi
    fi

    # Si pip no quedó instalado en el venv, instalarlo usando urllib de Python nativo (sin depender de curl/wget)
    if [ ! -f "$VENV_PIP" ]; then
        echo "📥 Descargando e instalando pip en el entorno virtual..."
        "$VENV_PYTHON" -c "
import urllib.request
url = 'https://bootstrap.pypa.io/get-pip.py'
urllib.request.urlretrieve(url, 'get-pip.py')
"
        "$VENV_PYTHON" get-pip.py --no-warn-script-location
        rm -f get-pip.py
    fi

    echo "⬇️  Instalando dependencias de Caelum (PySide6, Open-Meteo, etc.)..."
    "$VENV_PIP" install --upgrade pip
    "$VENV_PIP" install -r requirements.txt
    echo "✅ Entorno virtual configurado exitosamente."
fi

# 3. Comprobar librerías de sistema críticas para Qt6 en Linux (ej. libxcb-cursor en Mint/Ubuntu)
if [ -n "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    # Estamos en sesión X11 (como Linux Mint Cinnamon por defecto)
    if command -v ldconfig >/dev/null 2>&1; then
        if ! ldconfig -p 2>/dev/null | grep -q "libxcb-cursor.so.0"; then
            # Si no se encuentra en ldconfig, verificar rutas estándar
            if [ ! -f "/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0" ] && [ ! -f "/usr/lib/libxcb-cursor.so.0" ]; then
                echo "⚠️  Aviso: 'libxcb-cursor0' podría no estar instalada."
                if command -v apt >/dev/null 2>&1; then
                    echo "   Si la aplicación no abre en Linux Mint / Ubuntu, instala con:"
                    echo "   sudo apt install -y libxcb-cursor0"
                fi
            fi
        fi
    fi
fi

# Si se solicitó solo configuración/instalación previa
if [ "$1" = "--setup-only" ]; then
    echo "✅ Entorno de Caelum verificado y listo."
    exit 0
fi

# 4. Lanzar la aplicación
exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"
