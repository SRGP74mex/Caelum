import json
import logging
import os
from typing import Any, Dict, Optional

from PySide6.QtCore import QLocale, QObject, Signal

from config import IDIOMAS_SOPORTADOS, LOCALES_DIR

logger = logging.getLogger(__name__)


class I18nService(QObject):
    """
    Servicio de Internacionalización (i18n) para WeatherApp Linux.
    - Soporta 7 idiomas: Español (es), Inglés (en), Francés (fr), Italiano (it), Alemán (de), Portugués (pt) y Japonés (ja).
    - Detecta automáticamente el idioma del sistema operativo mediante QLocale.
    - Fallback inteligente en caso de claves no encontradas.
    - Interpolación de variables dinámica en plantillas {variable}.
    """
    idioma_cambiado = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.catalogos: Dict[str, Dict[str, Any]] = {}
        self.idioma_configurado: str = "auto"
        self.idioma_activo: str = "es"
        self._cargar_catalogos()
        self.establecer_idioma("auto")

    def _cargar_catalogos(self) -> None:
        """Carga todos los archivos JSON disponibles en assets/locales/."""
        if not LOCALES_DIR.exists():
            logger.warning("Directorio de locales no encontrado en %s", LOCALES_DIR)
            return

        for codigo in IDIOMAS_SOPORTADOS.keys():
            if codigo == "auto":
                continue
            archivo = LOCALES_DIR / f"{codigo}.json"
            if archivo.exists():
                try:
                    with open(archivo, "r", encoding="utf-8") as f:
                        self.catalogos[codigo] = json.load(f)
                    logger.debug("Catálogo i18n cargado: %s (%d secciones)", codigo, len(self.catalogos[codigo]))
                except Exception:
                    logger.exception("Error al leer archivo de traducción %s", archivo)

    def detectar_idioma_sistema(self) -> str:
        """Determina el código de idioma (es, en, fr, it, de, pt, ja) según el locale del sistema."""
        try:
            locale_name = QLocale.system().name().lower()  # Ej: "es_mx", "fr_fr", "ja_jp"
        except Exception:
            locale_name = os.environ.get("LANG", "en").lower()

        for lang in ["es", "en", "fr", "it", "de", "pt", "ja"]:
            if locale_name.startswith(lang):
                return lang

        # Si el idioma del sistema es otro, usar inglés como estándar internacional
        return "en"

    def establecer_idioma(self, codigo: str) -> None:
        """
        Establece el idioma activo. Si es 'auto', detecta el idioma del sistema.
        """
        self.idioma_configurado = codigo
        if codigo == "auto" or codigo not in self.catalogos:
            self.idioma_activo = self.detectar_idioma_sistema()
        else:
            self.idioma_activo = codigo

        logger.info("Idioma activo establecido: %s (configurado: %s)", self.idioma_activo, self.idioma_configurado)
        self.idioma_cambiado.emit(self.idioma_activo)

    def t(self, clave: str, **kwargs: Any) -> str:
        """
        Traduce una clave con notación de puntos (ej: 'cabecera.sensacion').
        Soporta reemplazo de variables con formato {nombre_variable}.
        """
        partes = clave.split(".")

        # 1. Buscar en el idioma activo
        texto = self._buscar_en_catalogo(self.idioma_activo, partes)

        # 2. Fallback a Inglés
        if texto is None and self.idioma_activo != "en":
            texto = self._buscar_en_catalogo("en", partes)

        # 3. Fallback a Español
        if texto is None and self.idioma_activo != "es":
            texto = self._buscar_en_catalogo("es", partes)

        # 4. Si no existe, devolver la última parte de la clave
        if texto is None:
            texto = partes[-1]

        # 5. Aplicar interpolación de variables si hay kwargs
        if kwargs and isinstance(texto, str):
            try:
                texto = texto.format(**kwargs)
            except Exception:
                pass

        return str(texto)

    def _buscar_en_catalogo(self, idioma: str, partes: list[str]) -> Optional[Any]:
        nodo = self.catalogos.get(idioma)
        if not nodo:
            return None
        for p in partes:
            if isinstance(nodo, dict) and p in nodo:
                nodo = nodo[p]
            else:
                return None
        return nodo


# Instancia Singleton Global
_i18n_instance: Optional[I18nService] = None


def get_i18n() -> I18nService:
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nService()
    return _i18n_instance


def t(clave: str, **kwargs: Any) -> str:
    """Función de acceso directo global para traducción de textos."""
    return get_i18n().t(clave, **kwargs)


def establecer_idioma(codigo: str) -> None:
    get_i18n().establecer_idioma(codigo)


def obtener_idioma_actual() -> str:
    return get_i18n().idioma_activo

