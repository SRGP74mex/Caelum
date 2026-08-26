"""Tests deterministas (sin red) para los servicios de red, usando unittest.mock
sobre la sesión HTTP compartida (src.servicios.http_session.sesion_http).

Complementan a tests/test_api.py, que sigue haciendo peticiones reales como
smoke test de integración (con skipTest si no hay red).
"""
import unittest
from unittest.mock import MagicMock, patch

import requests

from src.modelos.clima_datos import Ubicacion
from src.servicios.geocoding_service import GeocodingService
from src.servicios.http_session import sesion_http
from src.servicios.open_meteo_service import OpenMeteoService


def _respuesta_open_meteo_falsa() -> dict:
    horas = ["2026-08-26T00:00", "2026-08-26T01:00", "2026-08-26T02:00"]
    n = len(horas)
    return {
        "current": {
            "time": horas[0],
            "temperature_2m": 21.5,
            "relative_humidity_2m": 60,
            "apparent_temperature": 22.0,
            "is_day": 1,
            "precipitation": 0.0,
            "weather_code": 0,
            "surface_pressure": 1012.0,
            "pressure_msl": 1013.0,
            "wind_speed_10m": 10.0,
            "wind_direction_10m": 180,
            "wind_gusts_10m": 15.0,
        },
        "hourly": {
            "time": horas,
            "temperature_2m": [21.5] * n,
            "apparent_temperature": [22.0] * n,
            "relative_humidity_2m": [60] * n,
            "precipitation_probability": [10] * n,
            "precipitation": [0.0] * n,
            "weather_code": [0] * n,
            "visibility": [10000.0] * n,
            "uv_index": [3.0] * n,
            "is_day": [1] * n,
            "wind_speed_10m": [10.0] * n,
            "wind_direction_10m": [180] * n,
            "pressure_msl": [1013.0] * n,
        },
        "daily": {
            "time": ["2026-08-26"],
            "weather_code": [0],
            "temperature_2m_max": [25.0],
            "temperature_2m_min": [18.0],
            "sunrise": ["2026-08-26T06:30"],
            "sunset": ["2026-08-26T19:45"],
            "uv_index_max": [5.0],
            "precipitation_sum": [0.0],
            "precipitation_probability_max": [10],
        },
    }


class TestOpenMeteoConMocks(unittest.TestCase):
    def setUp(self):
        self.ubicacion = Ubicacion(
            ciudad="Madrid", pais="España", latitud=40.4168, longitud=-3.7038, timezone="Europe/Madrid"
        )
        self.service = OpenMeteoService()

    @patch.object(sesion_http, "get")
    def test_parseo_reporte_completo(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: _respuesta_open_meteo_falsa())

        reporte = self.service.obtener_reporte_completo(self.ubicacion)

        self.assertEqual(reporte.fuente, "Open-Meteo")
        self.assertEqual(reporte.actual.temperatura, 21.5)
        self.assertEqual(len(reporte.horas_24h), 3)
        self.assertEqual(len(reporte.dias_7d), 1)
        self.assertEqual(len(reporte.dias_7d[0].horas), 3)  # agrupación por fecha
        self.assertEqual(reporte.dias_7d[0].temp_max, 25.0)

    @patch.object(sesion_http, "get")
    def test_error_http_propaga_excepcion(self, mock_get):
        respuesta_falsa = MagicMock(status_code=500)
        respuesta_falsa.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = respuesta_falsa

        with self.assertRaises(requests.HTTPError):
            self.service.obtener_reporte_completo(self.ubicacion)


class TestGeocodingConMocks(unittest.TestCase):
    def setUp(self):
        self.geo = GeocodingService()

    @patch.object(sesion_http, "get")
    def test_open_meteo_geocoding_exitoso(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"results": [{
                "name": "Madrid", "country": "España", "admin1": "Comunidad de Madrid",
                "latitude": 40.4168, "longitude": -3.7038, "timezone": "Europe/Madrid",
            }]},
        )

        resultados = self.geo.buscar_ciudades("Madrid")

        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].ciudad, "Madrid")
        mock_get.return_value.raise_for_status.assert_called()

    @patch.object(sesion_http, "get")
    def test_fallback_a_nominatim_si_open_meteo_vacio(self, mock_get):
        def fake_get(url, *args, **kwargs):
            if "geocoding-api.open-meteo.com" in url:
                return MagicMock(status_code=200, json=lambda: {"results": []})
            if "nominatim.openstreetmap.org" in url:
                return MagicMock(status_code=200, json=lambda: [{
                    "name": "Springfield",
                    "address": {"city": "Springfield", "country": "Estados Unidos"},
                    "lat": "39.78", "lon": "-89.65",
                }])
            raise AssertionError(f"URL inesperada en el mock: {url}")

        mock_get.side_effect = fake_get

        resultados = self.geo.buscar_ciudades("Springfield xyz123")

        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].ciudad, "Springfield")

    @patch.object(sesion_http, "get")
    def test_detectar_ubicacion_ip_usa_segundo_proveedor_si_falla_el_primero(self, mock_get):
        def fake_get(url, *args, **kwargs):
            if "ipapi.co" in url:
                raise requests.exceptions.ConnectionError("fallo simulado del proveedor 1")
            if "ipwho.is" in url:
                return MagicMock(status_code=200, json=lambda: {
                    "success": True, "city": "Ciudad de México", "country": "México",
                    "latitude": 19.4326, "longitude": -99.1332,
                    "timezone": {"id": "America/Mexico_City"}, "region": "Ciudad de México",
                })
            raise AssertionError(f"URL inesperada en el mock: {url}")

        mock_get.side_effect = fake_get

        ubicacion = self.geo.detectar_ubicacion_ip()

        self.assertEqual(ubicacion.ciudad, "Ciudad de México")
        self.assertEqual(ubicacion.timezone, "America/Mexico_City")


if __name__ == "__main__":
    unittest.main()
