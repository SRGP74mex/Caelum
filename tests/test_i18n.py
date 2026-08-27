import json
import os
import unittest
from datetime import datetime

from PySide6.QtWidgets import QApplication

from config import IDIOMAS_SOPORTADOS, LOCALES_DIR
from src.servicios.i18n import I18nService, establecer_idioma, get_i18n, obtener_idioma_actual, t
from src.utils.astronomia_utils import AstronomiaHelper
from src.utils.fecha_utils import FechaHelper
from src.utils.icon_mapper import IconMapper

# Iniciar QApplication headless si es necesario
if not QApplication.instance():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    _app = QApplication([])


class TestI18nCatalogos(unittest.TestCase):
    """Pruebas de integridad de los catálogos JSON de idiomas."""

    def test_existencia_archivos_locales(self):
        for codigo in ["es", "en", "fr", "it", "de", "ja"]:
            archivo = LOCALES_DIR / f"{codigo}.json"
            self.assertTrue(archivo.exists(), f"El archivo {codigo}.json debe existir en {LOCALES_DIR}")
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)
                self.assertIn("app", data)
                self.assertIn("condiciones", data)
                self.assertIn("bento", data)
                self.assertIn("alertas", data)
                self.assertIn("ajustes", data)

    def test_consistencia_condiciones_wmo(self):
        wmo_codes = ["0", "1", "2", "3", "45", "51", "61", "65", "71", "75", "80", "95", "96", "99"]
        for codigo in ["es", "en", "fr", "it", "de", "ja"]:
            archivo = LOCALES_DIR / f"{codigo}.json"
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            conds = data.get("condiciones", {})
            for wmo in wmo_codes:
                self.assertIn(wmo, conds, f"WMO {wmo} no encontrado en catálogo {codigo}.json")


class TestI18nService(unittest.TestCase):
    """Pruebas funcionales del servicio de traducción en tiempo de ejecución."""

    def setUp(self):
        self.i18n = I18nService()

    def test_cambio_idioma_y_traduccion_simple(self):
        # Español
        self.i18n.establecer_idioma("es")
        self.assertEqual(self.i18n.idioma_activo, "es")
        self.assertEqual(self.i18n.t("comun.hoy"), "Hoy")
        self.assertEqual(self.i18n.t("condiciones.0"), "Despejado")

        # Inglés
        self.i18n.establecer_idioma("en")
        self.assertEqual(self.i18n.idioma_activo, "en")
        self.assertEqual(self.i18n.t("comun.hoy"), "Today")
        self.assertEqual(self.i18n.t("condiciones.0"), "Clear sky")

        # Francés
        self.i18n.establecer_idioma("fr")
        self.assertEqual(self.i18n.idioma_activo, "fr")
        self.assertEqual(self.i18n.t("comun.hoy"), "Aujourd'hui")
        self.assertEqual(self.i18n.t("condiciones.0"), "Ciel dégagé")

        # Italiano
        self.i18n.establecer_idioma("it")
        self.assertEqual(self.i18n.idioma_activo, "it")
        self.assertEqual(self.i18n.t("comun.hoy"), "Oggi")
        self.assertEqual(self.i18n.t("condiciones.0"), "Cielo sereno")

        # Alemán
        self.i18n.establecer_idioma("de")
        self.assertEqual(self.i18n.idioma_activo, "de")
        self.assertEqual(self.i18n.t("comun.hoy"), "Heute")
        self.assertEqual(self.i18n.t("condiciones.0"), "Klarer Himmel")

        # Japonés
        self.i18n.establecer_idioma("ja")
        self.assertEqual(self.i18n.idioma_activo, "ja")
        self.assertEqual(self.i18n.t("comun.hoy"), "今日")
        self.assertEqual(self.i18n.t("condiciones.0"), "快晴")

    def test_interpolacion_variables(self):
        self.i18n.establecer_idioma("es")
        res_es = self.i18n.t("cabecera.hoy_rango", max=24, min=12)
        self.assertIn("24", res_es)
        self.assertIn("12", res_es)
        self.assertIn("Máx", res_es)

        self.i18n.establecer_idioma("en")
        res_en = self.i18n.t("cabecera.hoy_rango", max=24, min=12)
        self.assertIn("H:", res_en)
        self.assertIn("L:", res_en)

        self.i18n.establecer_idioma("ja")
        res_ja = self.i18n.t("cabecera.hoy_rango", max=24, min=12)
        self.assertIn("最高:", res_ja)
        self.assertIn("最低:", res_ja)

    def test_fallback_clave_inexistente(self):
        self.i18n.establecer_idioma("ja")
        # Clave inexistente en todos
        res = self.i18n.t("modulo.clave_totalmente_inexistente")
        self.assertEqual(res, "clave_totalmente_inexistente")


class TestComponentesI18n(unittest.TestCase):
    """Verifica que los utilitarios y formateadores consumen el idioma seleccionado."""

    def test_icon_mapper_traduccion(self):
        establecer_idioma("es")
        cond_es = IconMapper.obtener_condicion(95, es_dia=True)
        self.assertEqual(cond_es.descripcion, "Tormenta eléctrica")

        establecer_idioma("en")
        cond_en = IconMapper.obtener_condicion(95, es_dia=True)
        self.assertEqual(cond_en.descripcion, "Thunderstorm")

        establecer_idioma("fr")
        cond_fr = IconMapper.obtener_condicion(95, es_dia=True)
        self.assertEqual(cond_fr.descripcion, "Orage")

        establecer_idioma("ja")
        cond_ja = IconMapper.obtener_condicion(95, es_dia=True)
        self.assertEqual(cond_ja.descripcion, "雷雨")

    def test_fechas_i18n(self):
        dt = datetime(2026, 8, 25) # Martes 25 de Agosto 2026

        establecer_idioma("es")
        greg_es = FechaHelper.fecha_gregoriana_legible(dt)
        self.assertIn("Mar", greg_es)
        self.assertIn("Ago", greg_es)

        establecer_idioma("en")
        greg_en = FechaHelper.fecha_gregoriana_legible(dt)
        self.assertIn("Tue", greg_en)
        self.assertIn("Aug", greg_en)

        establecer_idioma("fr")
        greg_fr = FechaHelper.fecha_gregoriana_legible(dt)
        self.assertIn("Mar", greg_fr)
        self.assertIn("Août", greg_fr)

        establecer_idioma("ja")
        greg_ja = FechaHelper.fecha_gregoriana_legible(dt)
        self.assertIn("2026年8月25日", greg_ja)
        self.assertIn("火", greg_ja)

    def test_astronomia_luna_i18n(self):
        establecer_idioma("es")
        luna_es = AstronomiaHelper.obtener_info_lunar()
        self.assertIsInstance(luna_es.nombre, str)

        establecer_idioma("ja")
        luna_ja = AstronomiaHelper.obtener_info_lunar()
        self.assertIsInstance(luna_ja.nombre, str)


if __name__ == "__main__":
    unittest.main()

