import unittest

from src.modelos.clima_datos import (
    ClimaActual,
    ReporteClimaCompleto,
    Ubicacion,
)
from src.utils.icon_mapper import IconMapper


class TestModelosClima(unittest.TestCase):
    def setUp(self):
        self.ubicacion = Ubicacion(
            ciudad="Bogotá",
            pais="Colombia",
            latitud=4.6097,
            longitud=-74.0817,
            timezone="America/Bogota"
        )
        self.condicion = IconMapper.obtener_condicion(2, es_dia=True)

    def test_ubicacion_creacion(self):
        self.assertEqual(self.ubicacion.ciudad, "Bogotá")
        self.assertEqual(self.ubicacion.latitud, 4.6097)

    def test_condicion_mapeo(self):
        self.assertEqual(self.condicion.wmo_code, 2)
        self.assertEqual(self.condicion.icon_name, "partly-cloudy-day")
        self.assertEqual(self.condicion.animacion_tipo, "clouds")

    def test_clima_actual_propiedades(self):
        clima = ClimaActual(
            temperatura=19.5,
            sensacion_termica=19.0,
            temp_max_hoy=21.0,
            temp_min_hoy=9.0,
            humedad_relativa=65,
            punto_rocio=12.5,
            viento_velocidad=14.0,
            viento_direccion=315, # Noroeste (NO)
            viento_rafagas=22.0,
            indice_uv=3.2,
            presion_hpa=1016.0,
            visibilidad_km=10.0,
            probabilidad_lluvia=20,
            precipitacion_mm=0.0,
            amanecer_iso="2026-08-25T05:55:00",
            ocaso_iso="2026-08-25T18:14:00",
            condicion=self.condicion
        )

        self.assertEqual(clima.uv_categoria, "Moderado")
        self.assertEqual(clima.viento_direccion_cardinal, "NO")

    def test_reporte_completo_estructura(self):
        clima = ClimaActual(
            temperatura=20.0,
            sensacion_termica=20.0,
            temp_max_hoy=22.0,
            temp_min_hoy=10.0,
            humedad_relativa=60,
            punto_rocio=11.0,
            viento_velocidad=10.0,
            viento_direccion=0, # Norte
            viento_rafagas=None,
            indice_uv=1.0,
            presion_hpa=1013.0,
            visibilidad_km=10.0,
            probabilidad_lluvia=0,
            precipitacion_mm=0.0,
            amanecer_iso="",
            ocaso_iso="",
            condicion=self.condicion
        )

        reporte = ReporteClimaCompleto(
            ubicacion=self.ubicacion,
            actual=clima,
            horas_24h=[],
            dias_7d=[]
        )

        self.assertEqual(reporte.ubicacion.ciudad, "Bogotá")
        self.assertEqual(reporte.fuente, "Open-Meteo")

if __name__ == "__main__":
    unittest.main()

