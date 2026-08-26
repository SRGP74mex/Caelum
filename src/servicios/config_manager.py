import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from src.modelos.clima_datos import Ubicacion

CONFIG_DIR = Path.home() / ".config" / "weather_linux"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ultima_ciudad": None,
    "ciudades_recientes": [],
    "ciudades_favoritas": [],
    "unidades": {
        "temperatura": "celsius",
        "viento": "kmh"
    },
    "mostrar_bandeja": True,
    "cerrar_a_bandeja": False
}

class ConfigManager:
    """
    Gestor de configuración persistente para WeatherApp Linux.
    Almacena preferencias, última ciudad y ciudades recientes en ~/.config/weather_linux/config.json.
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
                self.datos = dict(DEFAULT_CONFIG)

    def _guardar_dict(self, datos: Dict[str, Any]) -> None:
        try:
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

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
                pass
        return None

    def obtener_ciudades_recientes(self) -> List[Ubicacion]:
        """Obtiene la lista de ciudades recientemente consultadas."""
        res: List[Ubicacion] = []
        for d in self.datos.get("ciudades_recientes", []):
            try:
                res.append(Ubicacion(**d))
            except Exception:
                pass
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
                pass
        return res
