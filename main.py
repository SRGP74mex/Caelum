import faulthandler
import logging
import sys

# Habilitar faulthandler si stderr está disponible (en ejecutables GUI de Windows sys.stderr es None)
if sys.stderr is not None:
    try:
        faulthandler.enable()
    except Exception:
        pass

from src.utils.logging_config import configurar_logging  # noqa: E402

configurar_logging()  # Debe ejecutarse antes de importar el resto para capturar sus logs
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QApplication  # noqa: E402

from config import APP_ID, APP_NAME, STYLES_DIR  # noqa: E402
from src.utils.entorno_sistema import EntornoSistema  # noqa: E402
from src.utils.instancia_unica import GestorInstanciaUnica  # noqa: E402
from src.vistas.ventana_principal import VentanaPrincipal  # noqa: E402


def excepthook(exc_type, exc_value, exc_tb):
    logger.critical("Excepción no controlada interceptada", exc_info=(exc_type, exc_value, exc_tb))

sys.excepthook = excepthook

def cargar_estilos(app: QApplication) -> None:
    """Carga la hoja de estilos QSS principal de la aplicación."""
    qss_path = STYLES_DIR / "glassmorphism.qss"
    if qss_path.exists():
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception:
            logger.exception("No se pudo cargar la hoja de estilos")

def main():
    # 1. Configurar optimizaciones para Wayland, HiDPI y compositores Linux
    EntornoSistema.configurar_optimizaciones_wayland()

    logger.info("Iniciando %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName(APP_NAME)
    app.setDesktopFileName(APP_ID)

    servidor_grafico = EntornoSistema.obtener_servidor_grafico()
    escritorio = EntornoSistema.obtener_entorno_escritorio()
    logger.info("Entorno del sistema detectado: Servidor=%s, Escritorio=%s", servidor_grafico, escritorio)

    # 2. Comprobar si ya existe otra instancia en ejecución (Single-Instance IPC)
    gestor_instancia = GestorInstanciaUnica()
    if gestor_instancia.es_otra_instancia_activa():
        logger.info("Instancia previa detectada. Solicitud de activación enviada. Saliendo de la nueva instancia.")
        sys.exit(0)

    # Iniciar servidor local para recibir señales de futuras llamadas a la app
    gestor_instancia.iniciar_servidor()

    # Cargar estilos Glassmorphism
    cargar_estilos(app)

    # Crear y mostrar la ventana principal
    ventana = VentanaPrincipal()
    gestor_instancia.solicitud_activacion.connect(ventana.restaurar_y_enfocar)

    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
