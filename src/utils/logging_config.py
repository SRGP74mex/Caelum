import logging
import os
from logging.handlers import RotatingFileHandler

from config import CACHE_DIR

LOG_FILE = CACHE_DIR / "weatherapp.log"


def configurar_logging() -> None:
    """Configura el logging raíz de la aplicación: archivo rotativo + consola.

    Se debe llamar una única vez, al inicio de main.py. El nivel de consola
    es WARNING por defecto para no ensuciar la terminal; se puede subir a
    DEBUG con la variable de entorno WEATHER_LINUX_DEBUG=1.
    """
    nivel_consola = logging.DEBUG if os.environ.get("WEATHER_LINUX_DEBUG") == "1" else logging.WARNING
    formato = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handler_archivo = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler_archivo.setLevel(logging.DEBUG)
    handler_archivo.setFormatter(formato)

    raiz = logging.getLogger()
    raiz.setLevel(logging.DEBUG)
    raiz.addHandler(handler_archivo)

    import sys
    if sys.stdout is not None or sys.stderr is not None:
        handler_consola = logging.StreamHandler()
        handler_consola.setLevel(nivel_consola)
        handler_consola.setFormatter(formato)
        raiz.addHandler(handler_consola)

    # Silenciar ruido de librerías de terceros
    logging.getLogger("urllib3").setLevel(logging.WARNING)
