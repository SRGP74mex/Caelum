import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import asdict

from config import CACHE_DIR, CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)
from src.modelos.clima_datos import (
    Ubicacion,
    CondicionClimatica,
    ClimaActual,
    PronosticoHora,
    PronosticoDia,
    ReporteClimaCompleto,
)

class CacheManager:
    def __init__(self, cache_dir: Path = CACHE_DIR, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generar_clave(self, lat: float, lon: float) -> str:
        return f"weather_{round(lat, 2)}_{round(lon, 2)}.json"

    def guardar_reporte(self, reporte: ReporteClimaCompleto) -> None:
        """Guarda un reporte de clima serializado en disco con timestamp."""
        clave = self._generar_clave(reporte.ubicacion.latitud, reporte.ubicacion.longitud)
        archivo = self.cache_dir / clave

        payload = {
            "cached_at": time.time(),
            "reporte": asdict(reporte)
        }

        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.warning("No se pudo guardar caché en %s", archivo, exc_info=True)

    def obtener_reporte(self, lat: float, lon: float, ignorar_ttl: bool = False) -> Optional[ReporteClimaCompleto]:
        """Recupera el reporte cacheado si no ha expirado el TTL."""
        clave = self._generar_clave(lat, lon)
        archivo = self.cache_dir / clave

        if not archivo.exists():
            return None

        try:
            with open(archivo, "r", encoding="utf-8") as f:
                payload = json.load(f)

            cached_at = payload.get("cached_at", 0)
            if not ignorar_ttl and (time.time() - cached_at > self.ttl_seconds):
                return None # Expiró el caché

            data = payload.get("reporte", {})
            return self._reconstruir_reporte(data)
        except Exception:
            logger.warning("Caché corrupto o ilegible en %s", archivo, exc_info=True)
            return None

    def _reconstruir_reporte(self, data: Dict[str, Any]) -> ReporteClimaCompleto:
        """Reconstruye los objetos tipados a partir del diccionario serializado."""
        ub_data = data["ubicacion"]
        ubicacion = Ubicacion(**ub_data)

        act_data = data["actual"]
        cond_act_data = act_data.pop("condicion")
        cond_actual = CondicionClimatica(**cond_act_data)
        actual = ClimaActual(condicion=cond_actual, **act_data)

        horas_24h = []
        for h in data.get("horas_24h", []):
            h_copy = dict(h)
            h_cond = CondicionClimatica(**h_copy.pop("condicion"))
            horas_24h.append(PronosticoHora(condicion=h_cond, **h_copy))

        dias_7d = []
        for d in data.get("dias_7d", []):
            d_copy = dict(d)
            d_cond = CondicionClimatica(**d_copy.pop("condicion"))
            d_horas_raw = d_copy.pop("horas", [])
            d_horas = []
            for dh in d_horas_raw:
                dh_copy = dict(dh)
                dh_cond = CondicionClimatica(**dh_copy.pop("condicion"))
                d_horas.append(PronosticoHora(condicion=dh_cond, **dh_copy))
            dias_7d.append(PronosticoDia(condicion=d_cond, horas=d_horas, **d_copy))

        return ReporteClimaCompleto(
            ubicacion=ubicacion,
            actual=actual,
            horas_24h=horas_24h,
            dias_7d=dias_7d,
            fuente=data.get("fuente", "Open-Meteo (Caché)"),
            fecha_actualizacion_iso=data.get("fecha_actualizacion_iso", "")
        )

