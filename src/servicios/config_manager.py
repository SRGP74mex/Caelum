import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import directorio_datos_usuario
from src.modelos.clima_datos import Ubicacion

logger = logging.getLogger(__name__)

CONFIG_DIR = directorio_datos_usuario("config")
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ultima_ciudad": None,
    "ciudades_recientes": [],
    "ciudades_favoritas": [],
    "idioma": "auto",
    "unidades": {
        "temperatura": "celsius",
        "viento": "kmh"
    },
    "mostrar_bandeja": True,
    "cerrar_a_bandeja": False,
    "notificaciones": {
        "activadas": True,
        "alerta_lluvia": True,
        "alerta_tormenta": True,
        "alerta_atardecer": False
    },
    "calendarios": {
        "gregoriano": True,
        "hijri": True,
        "hebreo": True,
        "jalali": False,
        "budista": False,
        "etiope": False,
        "saka": False,
        "chino": False
    }
}

class ConfigManager:
    """
    Gestor de configuración persistente para Caelum.
    Almacena preferencias, última ciudad y ciudades recientes en ~/.config/caelum/config.json.
    """
    def __init__(self, ruta_archivo: Path = CONFIG_FILE):
        self.ruta_archivo = ruta_archivo
        self.config_dir = self.ruta_archivo.parent
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self._cargar_o_crear()

    def _cargar_o_crear(self) -> None:
        if not self.ruta_archivo.exists():
            self.datos = dict(DEFAULT_CONFIG)
            self._guardar_dict(self.datos)
        else:
            try:
                with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                    self.datos = json.load(f)
            except Exception:
                logger.warning("Config corrupta en %s, usando valores por defecto", self.ruta_archivo, exc_info=True)
                self.datos = dict(DEFAULT_CONFIG)

    def _guardar_dict(self, datos: Dict[str, Any]) -> None:
        try:
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.error("No se pudo escribir la configuración en %s", self.ruta_archivo, exc_info=True)

    def guardar_preferencias(
        self,
        unidades: Optional[Dict[str, str]] = None,
        mostrar_bandeja: Optional[bool] = None,
        cerrar_a_bandeja: Optional[bool] = None,
        notificaciones: Optional[Dict[str, bool]] = None,
        idioma: Optional[str] = None,
        calendarios: Optional[Dict[str, bool]] = None
    ) -> None:
        """Actualiza y persiste las preferencias generales del usuario."""
        if idioma is not None:
            self.datos["idioma"] = idioma
        if unidades is not None:
            self.datos["unidades"] = unidades
        if mostrar_bandeja is not None:
            self.datos["mostrar_bandeja"] = mostrar_bandeja
        if cerrar_a_bandeja is not None:
            self.datos["cerrar_a_bandeja"] = cerrar_a_bandeja
        if notificaciones is not None:
            self.datos["notificaciones"] = notificaciones
        if calendarios is not None:
            self.datos["calendarios"] = calendarios
        self._guardar_dict(self.datos)

    def obtener_calendarios_activos(self) -> Dict[str, bool]:
        """Retorna el diccionario de calendarios activos con valores por defecto."""
        defaults = dict(DEFAULT_CONFIG["calendarios"])
        guardados = self.datos.get("calendarios", {})
        defaults.update(guardados)
        return defaults

    def guardar_ultima_ciudad(self, ubicacion: Ubicacion) -> None:
        """Guarda la última ciudad y la añade al historial de recientes."""
        ub_dict = asdict(ubicacion)
        self.datos["ultima_ciudad"] = ub_dict

        # Actualizar lista de recientes (máx 6 sin duplicados)
        recientes = self.datos.get("ciudades_recientes", [])
        # Filtrar si ya existe
        recientes = [r for r in recientes if not (r.get("latitud") == ubicacion.latitud and r.get("longitud") == ubicacion.longitud)]
        recientes.insert(0, ub_dict)
        self.datos["ciudades_recientes"] = recientes[:6]

        self._guardar_dict(self.datos)

    def obtener_ultima_ciudad(self) -> Optional[Ubicacion]:
        """Recupera la última ciudad guardada por el usuario."""
        ub_data = self.datos.get("ultima_ciudad")
        if ub_data:
            try:
                return Ubicacion(**ub_data)
            except Exception:
                logger.debug("Entrada de 'ultima_ciudad' inválida en config", exc_info=True)
        return None

    def obtener_ciudades_recientes(self) -> List[Ubicacion]:
        """Obtiene la lista de ciudades recientemente consultadas."""
        res: List[Ubicacion] = []
        for d in self.datos.get("ciudades_recientes", []):
            try:
                res.append(Ubicacion(**d))
            except Exception:
                logger.debug("Entrada de 'ciudades_recientes' inválida en config", exc_info=True)
        return res

    def agregar_favorito(self, ubicacion: Ubicacion) -> None:
        favoritos = self.datos.get("ciudades_favoritas", [])
        ub_dict = asdict(ubicacion)
        if ub_dict not in favoritos:
            favoritos.append(ub_dict)
            self.datos["ciudades_favoritas"] = favoritos
            self._guardar_dict(self.datos)

    def obtener_favoritos(self) -> List[Ubicacion]:
        res: List[Ubicacion] = []
        for d in self.datos.get("ciudades_favoritas", []):
            try:
                res.append(Ubicacion(**d))
            except Exception:
                logger.debug("Entrada de 'ciudades_favoritas' inválida en config", exc_info=True)
        return res
