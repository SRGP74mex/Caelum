import logging
from datetime import datetime
from typing import Any, Dict, List

from dateutil import parser

from config import OPEN_METEO_BASE_URL, REQUEST_TIMEOUT
from src.modelos.clima_datos import (
    ClimaActual,
    PronosticoDia,
    PronosticoHora,
    ReporteClimaCompleto,
    Ubicacion,
)
from src.servicios.base_provider import IWeatherProvider
from src.servicios.http_session import sesion_http
from src.utils.fecha_utils import FechaHelper
from src.utils.icon_mapper import IconMapper

logger = logging.getLogger(__name__)

class OpenMeteoService(IWeatherProvider):
    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout

    def obtener_reporte_completo(self, ubicacion: Ubicacion) -> ReporteClimaCompleto:
        params = {
            "latitude": ubicacion.latitud,
            "longitude": ubicacion.longitud,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "weather_code",
                "surface_pressure",
                "pressure_msl",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m"
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "weather_code",
                "visibility",
                "uv_index",
                "is_day",
                "wind_speed_10m",
                "wind_direction_10m",
                "surface_pressure",
                "pressure_msl"
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "sunrise",
                "sunset",
                "uv_index_max",
                "precipitation_sum",
                "precipitation_probability_max"
            ],
            "timezone": ubicacion.timezone or "auto"
        }

        logger.debug("Consultando Open-Meteo para %s (%.4f, %.4f)", ubicacion.ciudad, ubicacion.latitud, ubicacion.longitud)
        response = sesion_http.get(OPEN_METEO_BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        return self._parse_json_a_reporte(data, ubicacion)

    def _parse_json_a_reporte(self, data: Dict[str, Any], ubicacion: Ubicacion) -> ReporteClimaCompleto:
        curr_data = data.get("current", {})
        hourly_data = data.get("hourly", {})
        daily_data = data.get("daily", {})

        # Listas de hourly
        times_hourly = hourly_data.get("time", [])
        temp_hourly = hourly_data.get("temperature_2m", [])
        apparent_hourly = hourly_data.get("apparent_temperature", [])
        humidity_hourly = hourly_data.get("relative_humidity_2m", [])
        precip_prob_hourly = hourly_data.get("precipitation_probability", [])
        precip_hourly = hourly_data.get("precipitation", [])
        wmo_hourly = hourly_data.get("weather_code", [])
        uv_hourly = hourly_data.get("uv_index", [])
        is_day_hourly = hourly_data.get("is_day", [])
        wind_speed_hourly = hourly_data.get("wind_speed_10m", [])
        wind_dir_hourly = hourly_data.get("wind_direction_10m", [])
        pressure_hourly = hourly_data.get("pressure_msl") or hourly_data.get("surface_pressure", [])
        vis_hourly = hourly_data.get("visibility", [])

        # Parsear todas las horas como objetos PronosticoHora
        todas_las_horas: List[PronosticoHora] = []
        for i in range(len(times_hourly)):
            t_iso = times_hourly[i]
            es_dia = bool(is_day_hourly[i]) if i < len(is_day_hourly) else True
            wmo = wmo_hourly[i] if i < len(wmo_hourly) else 0
            cond = IconMapper.obtener_condicion(wmo, es_dia=es_dia)
            etiqueta = FechaHelper.formato_hora_corta(t_iso)
            vis_km = round(float(vis_hourly[i]) / 1000.0, 1) if i < len(vis_hourly) and vis_hourly[i] is not None else 10.0

            hora = PronosticoHora(
                fecha_hora_iso=t_iso,
                hora_etiqueta=etiqueta,
                temperatura=float(temp_hourly[i]) if i < len(temp_hourly) else 0.0,
                sensacion=float(apparent_hourly[i]) if i < len(apparent_hourly) else 0.0,
                probabilidad_lluvia=int(precip_prob_hourly[i]) if i < len(precip_prob_hourly) and precip_prob_hourly[i] is not None else 0,
                precipitacion_mm=float(precip_hourly[i]) if i < len(precip_hourly) and precip_hourly[i] is not None else 0.0,
                condicion=cond,
                indice_uv=float(uv_hourly[i]) if i < len(uv_hourly) and uv_hourly[i] is not None else 0.0,
                es_noche=not es_dia,
                humedad_relativa=int(humidity_hourly[i]) if i < len(humidity_hourly) and humidity_hourly[i] is not None else 50,
                viento_velocidad=float(wind_speed_hourly[i]) if i < len(wind_speed_hourly) and wind_speed_hourly[i] is not None else 0.0,
                viento_direccion=int(wind_dir_hourly[i]) if i < len(wind_dir_hourly) and wind_dir_hourly[i] is not None else 0,
                presion_hpa=float(pressure_hourly[i]) if i < len(pressure_hourly) and pressure_hourly[i] is not None else 1013.25,
                visibilidad_km=vis_km
            )
            todas_las_horas.append(hora)

        # 1. Parsear Días (7 Días) y asociarles sus 24 horas correspondientes
        # Se agrupan las horas por fecha una sola vez (O(horas)) en vez de
        # recorrer todas_las_horas una vez por cada día (O(días × horas)).
        horas_por_fecha: Dict[str, List[PronosticoHora]] = {}
        for h in todas_las_horas:
            horas_por_fecha.setdefault(h.fecha_hora_iso[:10], []).append(h)

        dias_lista: List[PronosticoDia] = []
        fechas_diarias = daily_data.get("time", [])
        wmo_dias = daily_data.get("weather_code", [])
        temp_max_dias = daily_data.get("temperature_2m_max", [])
        temp_min_dias = daily_data.get("temperature_2m_min", [])
        sunrise_dias = daily_data.get("sunrise", [])
        sunset_dias = daily_data.get("sunset", [])
        uv_max_dias = daily_data.get("uv_index_max", [])
        precip_sum_dias = daily_data.get("precipitation_sum", [])
        precip_prob_dias = daily_data.get("precipitation_probability_max", [])

        for i, fecha_iso in enumerate(fechas_diarias):
            wmo = wmo_dias[i] if i < len(wmo_dias) else 0
            cond = IconMapper.obtener_condicion(wmo, es_dia=True)
            es_hoy = (i == 0)
            nombre_dia = FechaHelper.nombre_dia_pronostico(fecha_iso, es_hoy=es_hoy)

            # Horas que pertenecen a este día
            horas_dia = horas_por_fecha.get(fecha_iso, [])

            dia = PronosticoDia(
                fecha_iso=fecha_iso,
                nombre_dia=nombre_dia,
                temp_min=float(temp_min_dias[i]) if i < len(temp_min_dias) else 0.0,
                temp_max=float(temp_max_dias[i]) if i < len(temp_max_dias) else 0.0,
                probabilidad_lluvia=int(precip_prob_dias[i]) if i < len(precip_prob_dias) and precip_prob_dias[i] is not None else 0,
                precipitacion_total_mm=float(precip_sum_dias[i]) if i < len(precip_sum_dias) and precip_sum_dias[i] is not None else 0.0,
                amanecer_iso=sunrise_dias[i] if i < len(sunrise_dias) else "",
                ocaso_iso=sunset_dias[i] if i < len(sunset_dias) else "",
                indice_uv_max=float(uv_max_dias[i]) if i < len(uv_max_dias) and uv_max_dias[i] is not None else 0.0,
                condicion=cond,
                horas=horas_dia
            )
            dias_lista.append(dia)

        # 2. Parsear Horas consecutivas a partir de la hora actual (24 horas)
        ahora_iso = curr_data.get("time", datetime.now().isoformat())
        try:
            ahora_dt = parser.parse(ahora_iso)
        except Exception:
            ahora_dt = datetime.now()

        start_idx = 0
        for idx, t_str in enumerate(times_hourly):
            try:
                t_dt = parser.parse(t_str)
                if t_dt >= ahora_dt:
                    start_idx = max(0, idx - 1 if idx > 0 and (t_dt - ahora_dt).total_seconds() > 1800 else idx)
                    break
            except Exception:
                continue

        horas_24h_proximas: List[PronosticoHora] = []
        for count, i in enumerate(range(start_idx, min(len(todas_las_horas), start_idx + 24))):
            h_obj = todas_las_horas[i]
            # Clonar con etiqueta "Ahora" en la primera posición
            etiqueta = "Ahora" if count == 0 else h_obj.hora_etiqueta
            horas_24h_proximas.append(PronosticoHora(
                fecha_hora_iso=h_obj.fecha_hora_iso,
                hora_etiqueta=etiqueta,
                temperatura=h_obj.temperatura,
                sensacion=h_obj.sensacion,
                probabilidad_lluvia=h_obj.probabilidad_lluvia,
                precipitacion_mm=h_obj.precipitacion_mm,
                condicion=h_obj.condicion,
                indice_uv=h_obj.indice_uv,
                es_noche=h_obj.es_noche,
                humedad_relativa=h_obj.humedad_relativa,
                viento_velocidad=h_obj.viento_velocidad,
                viento_direccion=h_obj.viento_direccion,
                presion_hpa=h_obj.presion_hpa,
                visibilidad_km=h_obj.visibilidad_km
            ))

        # 3. Parsear Clima Actual
        wmo_actual = curr_data.get("weather_code", 0)
        es_dia_actual = bool(curr_data.get("is_day", 1))
        cond_actual = IconMapper.obtener_condicion(wmo_actual, es_dia=es_dia_actual)

        uv_actual = horas_24h_proximas[0].indice_uv if horas_24h_proximas else 0.0
        visibilidad_km = horas_24h_proximas[0].visibilidad_km if horas_24h_proximas else 10.0

        temp_val = float(curr_data.get("temperature_2m", 20.0))
        hum_val = int(curr_data.get("relative_humidity_2m", 50))
        punto_rocio = round(temp_val - ((100 - hum_val) / 5.0), 1)

        temp_max_hoy = dias_lista[0].temp_max if dias_lista else temp_val
        temp_min_hoy = dias_lista[0].temp_min if dias_lista else temp_val
        amanecer_hoy = dias_lista[0].amanecer_iso if dias_lista else ""
        ocaso_hoy = dias_lista[0].ocaso_iso if dias_lista else ""

        clima_actual = ClimaActual(
            temperatura=temp_val,
            sensacion_termica=float(curr_data.get("apparent_temperature", temp_val)),
            temp_max_hoy=temp_max_hoy,
            temp_min_hoy=temp_min_hoy,
            humedad_relativa=hum_val,
            punto_rocio=punto_rocio,
            viento_velocidad=float(curr_data.get("wind_speed_10m", 0.0)),
            viento_direccion=int(curr_data.get("wind_direction_10m", 0)),
            viento_rafagas=float(curr_data.get("wind_gusts_10m", 0.0)) if curr_data.get("wind_gusts_10m") is not None else None,
            indice_uv=uv_actual,
            presion_hpa=float(curr_data.get("pressure_msl") or curr_data.get("surface_pressure", 1013.25)),
            visibilidad_km=visibilidad_km,
            probabilidad_lluvia=horas_24h_proximas[0].probabilidad_lluvia if horas_24h_proximas else 0,
            precipitacion_mm=float(curr_data.get("precipitation", 0.0)),
            amanecer_iso=amanecer_hoy,
            ocaso_iso=ocaso_hoy,
            condicion=cond_actual,
            timestamp_iso=curr_data.get("time", datetime.now().isoformat())
        )

        return ReporteClimaCompleto(
            ubicacion=ubicacion,
            actual=clima_actual,
            horas_24h=horas_24h_proximas,
            dias_7d=dias_lista,
            fuente="Open-Meteo"
        )
