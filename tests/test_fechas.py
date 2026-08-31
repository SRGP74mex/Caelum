import unittest
from datetime import datetime

from src.servicios.i18n import establecer_idioma, obtener_idioma_actual
from src.utils.calendarios_mundo import (
    CalendarioHebreo,
)
from src.utils.fecha_utils import FechaHelper


class TestFechasUtils(unittest.TestCase):
    def setUp(self) -> None:
        # Los nombres de día/mes vienen de i18n, que autodetecta el idioma del
        # locale del sistema operativo (QLocale/LANG). En runners de CI el
        # locale por defecto suele ser inglés, así que se fija español de
        # forma explícita para que las aserciones no dependan del entorno.
        self._idioma_previo = obtener_idioma_actual()
        establecer_idioma("es")

    def tearDown(self) -> None:
        establecer_idioma(self._idioma_previo)

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

    def test_formato_jalali(self):
        dt = datetime(2026, 8, 27)
        jalali_str = FechaHelper.fecha_jalali_legible(dt)
        self.assertIn("1405 SH", jalali_str)
        self.assertIn("Shahrivar", jalali_str)
        self.assertIn("5", jalali_str)

    def test_formato_budista(self):
        dt = datetime(2026, 8, 27)
        budista_str = FechaHelper.fecha_budista_legible(dt)
        self.assertIn("2569 BE", budista_str)
        self.assertIn("27", budista_str)

    def test_formato_etiope(self):
        dt = datetime(2026, 8, 27)
        etiope_str = FechaHelper.fecha_etiope_legible(dt)
        self.assertIn("2018 EE", etiope_str)
        self.assertIn("Nehase", etiope_str)
        self.assertIn("21", etiope_str)

    def test_formato_saka(self):
        dt = datetime(2026, 8, 27)
        saka_str = FechaHelper.fecha_saka_legible(dt)
        self.assertIn("1948 Saka", saka_str)
        self.assertIn("Bhadra", saka_str)
        self.assertIn("5", saka_str)

    def test_formato_chino(self):
        dt = datetime(2026, 8, 27)
        chino_str = FechaHelper.fecha_china_legible(dt)
        self.assertIn("Caballo", chino_str)
        self.assertIn("15", chino_str)

    def test_obtener_pildoras_calendarios_filtrado(self):
        dt = datetime(2026, 8, 27)
        # Solo gregoriano y jalali activos
        config = {
            "gregoriano": True,
            "hijri": False,
            "hebreo": False,
            "jalali": True,
            "budista": False,
            "etiope": False,
            "saka": False,
            "chino": False,
        }
        pildoras = FechaHelper.obtener_pildoras_calendarios(dt, config)
        self.assertEqual(len(pildoras), 2)
        self.assertEqual(pildoras[0][0], "gregoriano")
        self.assertEqual(pildoras[0][1], "📅")
        self.assertEqual(pildoras[1][0], "jalali")
        self.assertEqual(pildoras[1][1], "☀️")

    def test_obtener_pildoras_todos_activos(self):
        dt = datetime(2026, 8, 27)
        config = {
            "gregoriano": True,
            "hijri": True,
            "hebreo": True,
            "jalali": True,
            "budista": True,
            "etiope": True,
            "saka": True,
            "chino": True,
        }
        pildoras = FechaHelper.obtener_pildoras_calendarios(dt, config)
        self.assertEqual(len(pildoras), 8)

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
