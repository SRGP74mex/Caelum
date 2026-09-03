#!/usr/bin/env bash
# ==============================================================================
# CAELUM - SCRIPT DE LANZAMIENTO Y AUTO-CONFIGURACIÓN UNIVERSAL
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# Aviso temprano: si el proyecto vive en una unidad FAT32/exFAT (típico de
# memorias USB usadas para llevar la carpeta entre equipos/VMs), "python3 -m
# venv" fallará SIEMPRE sin importar qué paquetes estén instalados, porque
# esos sistemas de archivos no soportan symlinks ni permisos Unix.
# ------------------------------------------------------------------------------
TIPO_FS="$(df --output=fstype "$SCRIPT_DIR" 2>/dev/null | tail -1 | tr -d '[:space:]')"
case "$TIPO_FS" in
    vfat|exfat|msdos|fat|fat32)
        echo "⚠️  Advertencia: esta carpeta está en una unidad $TIPO_FS ($SCRIPT_DIR)."
        echo "   Los sistemas FAT/exFAT no soportan symlinks ni permisos Unix, y la"
        echo "   creación del entorno virtual de Python (venv) fallará siempre aquí,"
        echo "   sin importar qué dependencias instales."
        echo "   👉 Copia esta carpeta a tu disco Linux (ej. tu \$HOME) y ejecútala desde ahí:"
        echo "      cp -r \"$SCRIPT_DIR\" ~/Caelum && cd ~/Caelum && ./install.sh"
        echo ""
        ;;
esac

# ------------------------------------------------------------------------------
# 0. Utilidades de detección de distro/gestor de paquetes e instalación
#    automática de dependencias de sistema, sin importar si es Ubuntu,
#    Linux Mint, Debian, Manjaro/Arch, Fedora u openSUSE.
# ------------------------------------------------------------------------------
SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

puede_instalar() {
    [ "$(id -u)" -eq 0 ] || [ -n "$SUDO" ]
}

detectar_gestor_paquetes() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v zypper >/dev/null 2>&1; then
        echo "zypper"
    else
        echo "desconocido"
    fi
}

GESTOR_PAQUETES="$(detectar_gestor_paquetes)"

# Instala uno o más paquetes con el gestor detectado. En Arch/Manjaro se evita
# forzar "-Sy" aislado (riesgo de actualización parcial); si la base local está
# muy desactualizada, se le pide al usuario un "pacman -Syu" completo.
instalar_paquetes() {
    case "$GESTOR_PAQUETES" in
        apt)
            $SUDO apt-get update -y || true
            $SUDO apt-get install -y "$@"
            ;;
        pacman)
            if ! $SUDO pacman -S --needed --noconfirm "$@"; then
                echo "⚠️  No se pudo instalar directamente. Ejecuta primero:"
                echo "      sudo pacman -Syu"
                echo "   y luego vuelve a correr este script."
                return 1
            fi
            ;;
        dnf)
            $SUDO dnf install -y "$@"
            ;;
        zypper)
            $SUDO zypper --non-interactive install "$@"
            ;;
        *)
            return 1
            ;;
    esac
}

# Comprueba si una librería compartida (.so) ya está resoluble en el sistema,
# sin depender del nombre de paquete (que varía entre distros/versiones).
# Nota: en usuarios no-root de Debian/Ubuntu, /sbin (donde vive ldconfig)
# suele faltar en el PATH, así que se prueban rutas explícitas también.
libreria_presente() {
    local so="$1"
    for ldconfig_bin in ldconfig /sbin/ldconfig /usr/sbin/ldconfig; do
        if command -v "$ldconfig_bin" >/dev/null 2>&1; then
            "$ldconfig_bin" -p 2>/dev/null | grep -q "$so" && return 0
            break
        fi
    done
    for ruta in /usr/lib /usr/lib64 /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu /usr/lib/i386-linux-gnu /usr/local/lib; do
        [ -f "$ruta/$so" ] && return 0
        for coincidencia in "$ruta/$so".*; do
            [ -e "$coincidencia" ] && return 0
        done
    done
    return 1
}

# ------------------------------------------------------------------------------
# 1. Librerías nativas que Qt6/PySide6 necesita para poder abrir ventana
#    (X11 y Wayland). Se verifican por librería real, no por nombre de paquete.
# ------------------------------------------------------------------------------
LIBS_QT_REQUERIDAS="libxcb-cursor.so.0 libEGL.so.1 libGL.so.1 libxkbcommon-x11.so.0 libxcb-icccm.so.4 libxcb-image.so.0 libxcb-keysyms.so.1 libxcb-randr.so.0 libxcb-render-util.so.0 libxcb-xinerama.so.0 libdbus-1.so.3"

paquetes_qt_sistema() {
    case "$GESTOR_PAQUETES" in
        apt) echo "libxcb-cursor0 libegl1 libgl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libdbus-1-3" ;;
        pacman) echo "xcb-util-cursor libxkbcommon-x11 mesa dbus" ;;
        dnf) echo "xcb-util-cursor libxkbcommon-x11 mesa-libGL mesa-libEGL dbus-libs" ;;
        zypper) echo "xcb-util-cursor libxkbcommon-x11-6 Mesa-libGL1 Mesa-libEGL1 dbus-1" ;;
        *) echo "" ;;
    esac
}

verificar_librerias_qt() {
    local falta=""
    for lib in $LIBS_QT_REQUERIDAS; do
        libreria_presente "$lib" || falta="$falta $lib"
    done

    if [ -z "$falta" ]; then
        return 0
    fi

    echo "📦 Librerías gráficas necesarias no encontradas:$falta"
    local paquetes
    paquetes="$(paquetes_qt_sistema)"

    if [ -z "$paquetes" ] || [ "$GESTOR_PAQUETES" = "desconocido" ]; then
        echo "⚠️  No se reconoció el gestor de paquetes; instala manualmente el equivalente a:$falta"
        return 1
    fi

    if ! puede_instalar; then
        echo "⚠️  No se encontró 'sudo' y no eres root. Instala manualmente:$paquetes"
        return 1
    fi

    echo "📥 Instalando vía $GESTOR_PAQUETES:$paquetes"
    instalar_paquetes $paquetes
}

echo "🔎 Verificando librerías gráficas del sistema ($GESTOR_PAQUETES)..."
if ! verificar_librerias_qt; then
    echo "⚠️  Continuando de todas formas; si la ventana no abre más abajo, instala lo indicado arriba."
fi

# ------------------------------------------------------------------------------
# 2. Comprobar que Python 3 está disponible; si no, intentar instalarlo solo.
# ------------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1 && puede_instalar; then
    echo "📥 Python 3 no encontrado. Instalando automáticamente..."
    case "$GESTOR_PAQUETES" in
        apt) instalar_paquetes python3 python3-venv python3-pip || true ;;
        pacman) instalar_paquetes python python-pip || true ;;
        dnf) instalar_paquetes python3 python3-pip || true ;;
        zypper) instalar_paquetes python3 python3-pip || true ;;
    esac
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error: Python 3 no está instalado en este sistema."
    case "$GESTOR_PAQUETES" in
        apt) echo "   👉 Instálalo ejecutando: sudo apt update && sudo apt install -y python3 python3-venv python3-pip" ;;
        pacman) echo "   👉 Instálalo ejecutando: sudo pacman -S python python-pip" ;;
        dnf) echo "   👉 Instálalo ejecutando: sudo dnf install -y python3 python3-pip" ;;
        zypper) echo "   👉 Instálalo ejecutando: sudo zypper install python3 python3-pip" ;;
        *) echo "   👉 Instala Python 3 con el gestor de paquetes de tu distribución." ;;
    esac
    exit 1
fi

# ------------------------------------------------------------------------------
# 3. Verificar y auto-crear el entorno virtual si no existe. Si falta el
#    módulo venv (común en Debian/Ubuntu/Mint sin python3-venv), se instala
#    automáticamente y se reintenta antes de rendirse.
# ------------------------------------------------------------------------------
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "📦 Preparando entorno virtual aislado para Caelum..."

    ERROR_VENV="$(python3 -m venv "$SCRIPT_DIR/venv" 2>&1)" || {
        echo "⚠️  No se pudo crear el entorno virtual con ensurepip:"
        echo "   $ERROR_VENV"

        if puede_instalar; then
            case "$GESTOR_PAQUETES" in
                apt) echo "📥 Instalando automáticamente: python3-venv python3-pip"; instalar_paquetes python3-venv python3-pip || true ;;
                pacman) echo "📥 Instalando automáticamente: python python-pip"; instalar_paquetes python python-pip || true ;;
                dnf) echo "📥 Instalando automáticamente: python3-pip"; instalar_paquetes python3-pip || true ;;
                zypper) echo "📥 Instalando automáticamente: python3-pip"; instalar_paquetes python3-pip || true ;;
            esac
        fi

        ERROR_VENV="$(python3 -m venv "$SCRIPT_DIR/venv" 2>&1)" || {
            echo "⚠️  Reintentando con --without-pip..."
            ERROR_VENV="$(python3 -m venv --without-pip "$SCRIPT_DIR/venv" 2>&1)" || {
                echo "❌ Error: no se pudo preparar el entorno virtual de Python en tu distribución."
                echo "   $ERROR_VENV"
                case "$GESTOR_PAQUETES" in
                    apt) echo "   👉 Ejecuta manualmente: sudo apt install -y python3-venv python3-pip" ;;
                    pacman) echo "   👉 Ejecuta manualmente: sudo pacman -S python python-pip" ;;
                    dnf) echo "   👉 Ejecuta manualmente: sudo dnf install -y python3-pip" ;;
                    zypper) echo "   👉 Ejecuta manualmente: sudo zypper install python3-pip" ;;
                esac
                exit 1
            }
        }
    }

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

# Si se solicitó solo configuración/instalación previa
if [ "$1" = "--setup-only" ]; then
    echo "✅ Entorno de Caelum verificado y listo."
    exit 0
fi

# 4. Lanzar la aplicación
exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"
