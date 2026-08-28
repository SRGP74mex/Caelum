import unittest
from datetime import datetime

from src.utils.fecha_utils import FechaHelper
from src.utils.hebrew_converter import CalendarioHebreo


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

    def test_formato_hebreo(self):
        dt = datetime(2026, 8, 27)
        hebrea_str = FechaHelper.fecha_hebrea_legible(dt)
        self.assertIn("5786 AM", hebrea_str)
        self.assertIn("Elul", hebrea_str)
        self.assertIn("14", hebrea_str)

    def test_fechas_calendarios_completas(self):
        dt = datetime(2026, 8, 27)
        greg, hijri, hebrea = FechaHelper.fechas_calendarios_completas(dt)
        self.assertTrue(len(greg) > 0)
        self.assertTrue(len(hijri) > 0)
        self.assertTrue(len(hebrea) > 0)
        self.assertIn("2026", greg)
        self.assertIn("1448 AH", hijri)
        self.assertIn("5786 AM", hebrea)

    def test_calendario_hebreo_festividades_exactas(self):
        # 1 Tishrei 5784 -> 16 Sep 2023 (Rosh Hashaná 5784)
        y, m, d = CalendarioHebreo.de_gregoriano(2023, 9, 16)
        self.assertEqual((y, m, d), (5784, 7, 1))

        # 25 Kislev 5784 -> 8 Dec 2023 (Janucá)
        y, m, d = CalendarioHebreo.de_gregoriano(2023, 12, 8)
        self.assertEqual((y, m, d), (5784, 9, 25))

        # 15 Nisan 5784 -> 23 Apr 2024 (Pésaj)
        y, m, d = CalendarioHebreo.de_gregoriano(2024, 4, 23)
        self.assertEqual((y, m, d), (5784, 1, 15))

    def test_nombre_dia_pronostico(self):
        self.assertEqual(FechaHelper.nombre_dia_pronostico("2026-08-25", es_hoy=True), "Hoy")
        self.assertEqual(FechaHelper.nombre_dia_pronostico("2026-08-25", es_hoy=False), "Mar")

    def test_formato_hora_corta(self):
        hora = FechaHelper.formato_hora_corta("2026-08-25T14:30:00")
        self.assertEqual(hora, "14:30")


if __name__ == "__main__":
    unittest.main()
