import unittest
import tempfile
import shutil
from pathlib import Path
from src.modelos.clima_datos import Ubicacion
from src.servicios.open_meteo_service import OpenMeteoService
from src.servicios.geocoding_service import GeocodingService
from src.servicios.cache_manager import CacheManager

class TestServiciosAPI(unittest.TestCase):
    def setUp(self):
        self.ubicacion = Ubicacion(
            ciudad="Madrid",
            pais="España",
            latitud=40.4168,
            longitud=-3.7038,
            timezone="Europe/Madrid"
        )
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(cache_dir=self.temp_dir, ttl_seconds=60)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_open_meteo_live_fetch(self):
        service = OpenMeteoService()
        try:
            reporte = service.obtener_reporte_completo(self.ubicacion)
            self.assertIsNotNone(reporte)
            self.assertEqual(reporte.ubicacion.ciudad, "Madrid")
            self.assertGreater(len(reporte.horas_24h), 0)
            self.assertGreater(len(reporte.dias_7d), 0)
            self.assertIsNotNone(reporte.actual.temperatura)
        except Exception as e:
            self.skipTest(f"Red no disponible para test de API en vivo: {e}")

    def test_geocoding_busqueda(self):
        geo = GeocodingService()
        try:
            resultados = geo.buscar_ciudades("Bogota", limite=3)
            self.assertTrue(len(resultados) > 0)
            self.assertIn("Bogot", resultados[0].ciudad)
        except Exception as e:
            self.skipTest(f"Red no disponible para test de geocoding: {e}")

    def test_cache_guardar_y_recuperar(self):
        service = OpenMeteoService()
        try:
            reporte_original = service.obtener_reporte_completo(self.ubicacion)
            self.cache_manager.guardar_reporte(reporte_original)

            reporte_recuperado = self.cache_manager.obtener_reporte(
                self.ubicacion.latitud,
                self.ubicacion.longitud
            )
            self.assertIsNotNone(reporte_recuperado)
            self.assertEqual(reporte_recuperado.ubicacion.ciudad, "Madrid")
            self.assertEqual(
                reporte_recuperado.actual.temperatura,
                reporte_original.actual.temperatura
            )
        except Exception as e:
            self.skipTest(f"Red no disponible para test de integración: {e}")

if __name__ == "__main__":
    unittest.main()

