#!/usr/bin/env bash
# ==============================================================================
# CAELUM - INSTALADOR DE LANZADOR DE ESCRITORIO
#
# Genera caelum.desktop con la ruta absoluta real del proyecto en esta
# máquina (en vez de tener una ruta fija hardcodeada) y lo registra para el
# usuario actual en ~/.local/share/applications.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/caelum.desktop"
TARGET_DIR="$HOME/.local/share/applications"
TARGET_FILE="$TARGET_DIR/caelum.desktop"

# Asegurar que el entorno virtual y dependencias estén instaladas
"$SCRIPT_DIR/run.sh" --setup-only || true

cat > "$DESKTOP_FILE" <<EOF
#!/usr/bin/env xdg-open
[Desktop Entry]
Name=Caelum
Comment=Aplicación de clima y astronomía moderna, fluida y rápida para Linux
Exec=/bin/bash -c "cd '$SCRIPT_DIR' && ./run.sh"
Icon=$SCRIPT_DIR/assets/icons/weather_app.svg
Terminal=false
Type=Application
Categories=Utility;Weather;Astronomy;Qt;
StartupWMClass=caelum
StartupNotify=true
Keywords=weather;clima;astronomia;pronostico;forecast;caelum;glassmorphism;
EOF
chmod 644 "$DESKTOP_FILE"

mkdir -p "$TARGET_DIR"
cp "$DESKTOP_FILE" "$TARGET_FILE"
chmod 644 "$TARGET_FILE"

# Retirar lanzadores del nombre antiguo del proyecto ("Weather Linux"), que
# duplicaban la entrada de Caelum en el menú de aplicaciones
for antiguo in weather-linux.desktop com.weatherlinux.app.desktop; do
    if [ -L "$TARGET_DIR/$antiguo" ] || grep -q "Name=Caelum" "$TARGET_DIR/$antiguo" 2>/dev/null; then
        rm -f "$TARGET_DIR/$antiguo"
    fi
done

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
