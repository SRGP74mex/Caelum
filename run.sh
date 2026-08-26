#!/usr/bin/env bash
# ==============================================================================
# WEATHERAPP LINUX - SCRIPT DE LANZAMIENTO
# ==============================================================================

set -e

# Obtener directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar si existe el entorno virtual
if [ ! -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    echo "⚠️  Entorno virtual no encontrado. Creando venv e instalando dependencias..."
    python3 -m venv --without-pip venv
    curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    ./venv/bin/python3 get-pip.py
    ./venv/bin/pip install -r requirements.txt
    rm get-pip.py
    echo "✅ Entorno virtual listo."
fi

# Lanzar la aplicación
exec "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/main.py" "$@"

