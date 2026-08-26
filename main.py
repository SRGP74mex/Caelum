import sys
import os
import faulthandler
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Habilitar faulthandler para capturar trazas de diagnóstico
faulthandler.enable()

from config import STYLES_DIR, APP_NAME, APP_ID
from src.vistas.ventana_principal import VentanaPrincipal

def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    print("⚠️ Excepción no controlada interceptada:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook

def cargar_estilos(app: QApplication) -> None:
    """Carga la hoja de estilos QSS principal de la aplicación."""
    qss_path = STYLES_DIR / "glassmorphism.qss"
    if qss_path.exists():
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"⚠️ No se pudo cargar la hoja de estilos: {e}")

def main():
    # Soporte para HiDPI en escritorios Linux
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setDesktopFileName("weather-linux")

    # Cargar estilos Glassmorphism
    cargar_estilos(app)

    # Crear y mostrar la ventana principal
    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
