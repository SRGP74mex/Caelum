import unittest

from src.modelos.clima_datos import (
    ClimaActual,
    CondicionClimatica,
    PronosticoDia,
    PronosticoHora,
    ReporteClimaCompleto,
    Ubicacion,
)
from src.utils import unidades


class TestConversionesUnidades(unittest.TestCase):
    def tearDown(self):
        # Restaurar estado por defecto para no afectar otros tests del módulo.
        unidades.establecer_preferencias_unidades({"temperatura": "celsius", "viento": "kmh"})

    def test_convertir_temperatura_celsius_a_fahrenheit(self):
        self.assertAlmostEqual(unidades.convertir_temperatura(0, "fahrenheit"), 32.0)
        self.assertAlmostEqual(unidades.convertir_temperatura(100, "fahrenheit"), 212.0)
        self.assertAlmostEqual(unidades.convertir_temperatura(20, "celsius"), 20.0)

    def test_celsius_desde_es_inversa_de_convertir_temperatura(self):
        for valor_c in (-10, 0, 21.5, 40):
            valor_f = unidades.convertir_temperatura(valor_c, "fahrenheit")
            self.assertAlmostEqual(unidades.celsius_desde(valor_f, "fahrenheit"), valor_c)

    def test_convertir_viento(self):
        self.assertAlmostEqual(unidades.convertir_viento(36, "ms"), 10.0)
        self.assertAlmostEqual(unidades.convertir_viento(10, "mph"), 6.2137, places=3)
        self.assertAlmostEqual(unidades.convertir_viento(10, "kmh"), 10.0)

    def test_sufijos_reflejan_preferencia_activa(self):
        unidades.establecer_preferencias_unidades({"temperatura": "fahrenheit", "viento": "mph"})
        self.assertEqual(unidades.sufijo_temperatura(), "°F")
        self.assertEqual(unidades.sufijo_viento(), "mph")

    def test_aplicar_preferencias_unidades_no_muta_el_reporte_original(self):
        condicion = CondicionClimatica(wmo_code=0, descripcion="Despejado", icon_name="clear-day")
        actual = ClimaActual(
            temperatura=20.0, sensacion_termica=19.0, temp_max_hoy=25.0, temp_min_hoy=15.0,
            humedad_relativa=50, punto_rocio=10.0, viento_velocidad=18.0, viento_direccion=180,
            viento_rafagas=None, indice_uv=5.0, presion_hpa=1013.0, visibilidad_km=10.0,
            probabilidad_lluvia=0, precipitacion_mm=0.0, amanecer_iso="", ocaso_iso="", condicion=condicion,
        )
        hora = PronosticoHora(
            fecha_hora_iso="2026-08-26T12:00", hora_etiqueta="12:00", temperatura=20.0, sensacion=19.0,
            probabilidad_lluvia=0, precipitacion_mm=0.0, condicion=condicion, viento_velocidad=18.0,
        )
        dia = PronosticoDia(
            fecha_iso="2026-08-26", nombre_dia="Hoy", temp_min=15.0, temp_max=25.0,
            probabilidad_lluvia=0, precipitacion_total_mm=0.0, amanecer_iso="", ocaso_iso="",
            indice_uv_max=5.0, condicion=condicion, horas=[hora],
        )
        reporte = ReporteClimaCompleto(
            ubicacion=Ubicacion(ciudad="Madrid", pais="España", latitud=40.4, longitud=-3.7),
            actual=actual, horas_24h=[hora], dias_7d=[dia],
        )

        unidades.establecer_preferencias_unidades({"temperatura": "fahrenheit", "viento": "ms"})
        reporte_convertido = unidades.aplicar_preferencias_unidades(reporte)

        # El original permanece intacto (para no corromper el caché en disco).
        self.assertEqual(reporte.actual.temperatura, 20.0)
        self.assertEqual(reporte.dias_7d[0].horas[0].temperatura, 20.0)

        # La copia devuelta sí está convertida.
        self.assertAlmostEqual(reporte_convertido.actual.temperatura, 68.0)
        self.assertAlmostEqual(reporte_convertido.actual.viento_velocidad, 5.0)
        self.assertAlmostEqual(reporte_convertido.dias_7d[0].horas[0].temperatura, 68.0)


if __name__ == "__main__":
    unittest.main()
