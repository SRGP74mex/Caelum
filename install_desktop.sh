#!/usr/bin/env bash
# ==============================================================================
# WEATHERAPP LINUX - INSTALADOR DE LANZADOR DE ESCRITORIO
#
# Genera weather-linux.desktop con la ruta absoluta real del proyecto en esta
# máquina (en vez de tener una ruta fija hardcodeada) y lo registra para el
# usuario actual en ~/.local/share/applications.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/weather-linux.desktop"
TARGET_DIR="$HOME/.local/share/applications"
TARGET_FILE="$TARGET_DIR/weather-linux.desktop"

cat > "$DESKTOP_FILE" <<EOF
#!/usr/bin/env xdg-open
[Desktop Entry]
Name=Weather Linux
GenericName=Aplicación de Clima
Comment=Aplicación de clima estilo Apple para Linux con PySide6
Exec=/bin/bash -c "cd '$SCRIPT_DIR' && ./run.sh"
Icon=$SCRIPT_DIR/assets/icons/weather_app.svg
Terminal=false
Type=Application
Categories=Utility;Weather;Qt;
StartupWMClass=weather-linux
StartupNotify=true
Keywords=weather;clima;pronostico;forecast;apple;
EOF
chmod 644 "$DESKTOP_FILE"

mkdir -p "$TARGET_DIR"
cp "$DESKTOP_FILE" "$TARGET_FILE"
chmod 644 "$TARGET_FILE"

# Crear también enlace para com.weatherlinux.app.desktop por compatibilidad
ln -sf "$TARGET_FILE" "$TARGET_DIR/com.weatherlinux.app.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$TARGET_DIR" >/dev/null 2>&1 || true
fi

# Notificar al gestor de KDE Plasma si está presente
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental >/dev/null 2>&1 || true
fi

echo "✅ Lanzador instalado en: $TARGET_FILE"
echo "   (apunta a: $SCRIPT_DIR)"
