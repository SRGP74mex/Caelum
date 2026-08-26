import unittest
from datetime import datetime

from src.utils.fecha_utils import FechaHelper


class TestFechasUtils(unittest.TestCase):
    def test_formato_gregoriano(self):
        dt = datetime(2026, 8, 25, 18, 0, 0)
        legible = FechaHelper.fecha_gregoriana_legible(dt)
        self.assertIn("Martes", legible)
        self.assertIn("25 de Agosto de 2026", legible)

    def test_formato_hijri(self):
        dt = datetime(2026, 8, 25)
        hijri_str = FechaHelper.fecha_hijri_legible(dt)
        self.assertIn("1448 AH", hijri_str)
        self.assertIn("Rabi' al-Awwal", hijri_str)

    def test_fecha_dual(self):
        dt = datetime(2026, 8, 25)
        greg, hijri = FechaHelper.fecha_dual_completa(dt)
        self.assertTrue(len(greg) > 0)
        self.assertTrue(len(hijri) > 0)

    def test_nombre_dia_pronostico(self):
        self.assertEqual(FechaHelper.nombre_dia_pronostico("2026-08-25", es_hoy=True), "Hoy")
        self.assertEqual(FechaHelper.nombre_dia_pronostico("2026-08-25", es_hoy=False), "Mar")

    def test_formato_hora_corta(self):
        hora = FechaHelper.formato_hora_corta("2026-08-25T14:30:00")
        self.assertEqual(hora, "14:30")

if __name__ == "__main__":
    unittest.main()
