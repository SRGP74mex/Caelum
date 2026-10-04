#!/usr/bin/env bash
# ==============================================================================
# CAELUM - INSTALADOR LOCAL (estilo AppImage)
#
# Copia la app a ~/.local/share/caelum (sin necesitar sudo ni tocar el
# sistema), crea/actualiza su propio entorno virtual ahí, y registra un
# lanzador con ícono en el menú de aplicaciones. Volver a ejecutar este
# script actualiza una instalación existente con lo último de este checkout.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/caelum"
DESKTOP_TARGET_DIR="$HOME/.local/share/applications"
DESKTOP_TARGET_FILE="$DESKTOP_TARGET_DIR/caelum.desktop"

echo "📦 Instalando Caelum en: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 1. Copiar los archivos necesarios para ejecutar la app (sin venv/tests/.git)
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude venv \
        "$SCRIPT_DIR/main.py" "$SCRIPT_DIR/config.py" "$SCRIPT_DIR/run.sh" \
        "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/src" "$SCRIPT_DIR/assets" \
        "$INSTALL_DIR/"
else
    cp -f "$SCRIPT_DIR/main.py" "$SCRIPT_DIR/config.py" "$SCRIPT_DIR/run.sh" "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/src" "$SCRIPT_DIR/assets" "$INSTALL_DIR/"
fi
chmod +x "$INSTALL_DIR/run.sh"

# 2. Crear/verificar el entorno virtual propio de la instalación
"$INSTALL_DIR/run.sh" --setup-only

# 3. Mantener dependencias al día en cada instalación/actualización
echo "⬇️  Verificando dependencias al día..."
"$INSTALL_DIR/venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"

# 4. Registrar el lanzador de escritorio (ícono + entrada en el menú)
mkdir -p "$DESKTOP_TARGET_DIR"
cat > "$DESKTOP_TARGET_FILE" <<EOF
#!/usr/bin/env xdg-open
[Desktop Entry]
Name=Caelum
Comment=Aplicación de clima y astronomía moderna, fluida y rápida para Linux
Exec=/bin/bash -c "cd '$INSTALL_DIR' && ./run.sh"
Icon=$INSTALL_DIR/assets/icons/weather_app.svg
Terminal=false
Type=Application
Categories=Utility;Weather;Astronomy;Qt;
StartupWMClass=caelum
StartupNotify=true
Keywords=weather;clima;astronomia;pronostico;forecast;caelum;glassmorphism;
EOF
chmod 644 "$DESKTOP_TARGET_FILE"

# Retirar lanzadores del nombre antiguo del proyecto ("Weather Linux"), que
# duplicaban la entrada de Caelum en el menú de aplicaciones
for antiguo in weather-linux.desktop com.weatherlinux.app.desktop; do
    if [ -L "$DESKTOP_TARGET_DIR/$antiguo" ] || grep -q "Name=Caelum" "$DESKTOP_TARGET_DIR/$antiguo" 2>/dev/null; then
        rm -f "$DESKTOP_TARGET_DIR/$antiguo"
    fi
done

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_TARGET_DIR" >/dev/null 2>&1 || true
fi

# Notificar al gestor de KDE Plasma si está presente
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental >/dev/null 2>&1 || true
fi

echo "✅ Caelum instalado/actualizado en: $INSTALL_DIR"
echo "   Búscalo como 'Caelum' en tu menú de aplicaciones."
echo "   (Para actualizar más adelante, vuelve a correr este mismo script)"
