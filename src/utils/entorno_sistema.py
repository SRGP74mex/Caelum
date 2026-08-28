import logging
import os
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QSystemTrayIcon

logger = logging.getLogger(__name__)


class EntornoSistema:
    """
    Detector y optimizador de entorno de ejecución para Linux:
    - Identifica el servidor gráfico activo (Wayland vs X11).
    - Identifica el entorno de escritorio (GNOME, KDE Plasma, XFCE, Cinnamon, etc.).
    - Proporciona optimizaciones nativas de escalado HiDPI y compatibilidad de ventanas.
    """

    @staticmethod
    def configurar_optimizaciones_wayland() -> None:
        """
        Aplica políticas Qt antes de instanciar QApplication.
        Mejora el escalado fraccional y la respuesta bajo compositores Wayland y X11.
        """
        # Escalado fraccional nítido en pantallas 2K/4K
        try:
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception:
            pass

    @staticmethod
    def es_wayland() -> bool:
        """Determina si la sesión actual se está ejecutando sobre Wayland."""
        plataforma_qt = ""
        app = QGuiApplication.instance()
        if app:
            plataforma_qt = QGuiApplication.platformName().lower()

        if "wayland" in plataforma_qt:
            return True

        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            return True

        if "WAYLAND_DISPLAY" in os.environ:
            return True

        return False

    @staticmethod
    def es_x11() -> bool:
        """Determina si la sesión actual se está ejecutando sobre X11."""
        if EntornoSistema.es_wayland():
            return False

        plataforma_qt = ""
        app = QGuiApplication.instance()
        if app:
            plataforma_qt = QGuiApplication.platformName().lower()

        if "xcb" in plataforma_qt or "x11" in plataforma_qt:
            return True

        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "x11":
            return True

        return "DISPLAY" in os.environ

    @staticmethod
    def obtener_servidor_grafico() -> str:
        """Retorna el nombre legible del servidor gráfico (Wayland, X11, etc.)."""
        if EntornoSistema.es_wayland():
            return "Wayland"
        elif EntornoSistema.es_x11():
            return "X11 (XCB)"
        
        app = QGuiApplication.instance()
        if app:
            plat = QGuiApplication.platformName()
            if plat:
                return plat.capitalize()
        return "Desconocido"

    @staticmethod
    def obtener_entorno_escritorio() -> str:
        """
        Retorna el nombre del Entorno de Escritorio o Compositor (GNOME, KDE Plasma, XFCE, etc.).
        """
        escritorio_raw = os.environ.get("XDG_CURRENT_DESKTOP", "") or os.environ.get("DESKTOP_SESSION", "")
        escritorio_upper = escritorio_raw.upper()

        if "GNOME" in escritorio_upper:
            return "GNOME"
        elif "KDE" in escritorio_upper or "PLASMA" in escritorio_upper:
            return "KDE Plasma"
        elif "XFCE" in escritorio_upper:
            return "XFCE"
        elif "CINNAMON" in escritorio_upper:
            return "Cinnamon"
        elif "MATE" in escritorio_upper:
            return "MATE"
        elif "LXQT" in escritorio_upper:
            return "LXQt"
        elif "HYPRLAND" in escritorio_upper:
            return "Hyprland"
        elif "SWAY" in escritorio_upper:
            return "Sway"
        elif "I3" in escritorio_upper:
            return "i3"
        elif "PANTHEON" in escritorio_upper:
            return "Pantheon"
        elif "COSMIC" in escritorio_upper:
            return "COSMIC"
        
        return escritorio_raw if escritorio_raw else "Linux Desktop"

    @staticmethod
    def soporta_system_tray() -> bool:
        """Verifica si el sistema tiene soporte activo para bandeja del sistema."""
        try:
            return QSystemTrayIcon.isSystemTrayAvailable()
        except Exception:
            return False

    @staticmethod
    def obtener_info_completa() -> Dict[str, Any]:
        """Retorna un diccionario con los detalles del entorno del sistema."""
        return {
            "servidor_grafico": EntornoSistema.obtener_servidor_grafico(),
            "es_wayland": EntornoSistema.es_wayland(),
            "es_x11": EntornoSistema.es_x11(),
            "escritorio": EntornoSistema.obtener_entorno_escritorio(),
            "soporte_bandeja": EntornoSistema.soporta_system_tray()
        }
