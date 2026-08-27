import os
import sys
import unittest
from datetime import datetime, timezone

from PySide6.QtWidgets import QApplication

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from config import LUNA_DIR
from src.componentes.bento_grid import BentoGridWidget
from src.componentes.curva_horaria import CurvaHorariaWidget
from src.componentes.tarjetas_metricas import TarjetaCalidadAire, TarjetaFaseLunar
from src.modelos.clima_datos import (
    ClimaActual,
    CondicionClimatica,
    DatosCalidadAire,
    PronosticoDia,
    PronosticoHora,
    ReporteClimaCompleto,
    Ubicacion,
)
from src.servicios.calidad_aire_service import CalidadAireService
from src.servicios.config_manager import ConfigManager
from src.utils.astronomia_utils import AstronomiaHelper
from src.vistas.vista_ajustes import VistaAjustes


class TestNuevasFuncionalidades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.ubicacion = Ubicacion(
            ciudad="Madrid",
            pais="España",
            latitud=40.4168,
            longitud=-3.7038,
            timezone="Europe/Madrid"
        )
        self.condicion = CondicionClimatica(
            wmo_code=0,
            descripcion="Despejado",
            icon_name="clear-day",
            es_dia=True,
            animacion_tipo="clear"
        )
        self.calidad_aire = DatosCalidadAire(
            aqi_europeo=22,
            aqi_us=42,
            pm2_5=6.8,
            pm10=12.4
        )
        self.actual = ClimaActual(
            temperatura=24.0,
            sensacion_termica=24.5,
            temp_max_hoy=28.0,
            temp_min_hoy=16.0,
            humedad_relativa=45,
            punto_rocio=13.0,
            viento_velocidad=12.0,
            viento_direccion=180,
            viento_rafagas=18.0,
            indice_uv=4.0,
            presion_hpa=1016.0,
            visibilidad_km=10.0,
            probabilidad_lluvia=0,
            precipitacion_mm=0.0,
            amanecer_iso="2026-08-26T07:00:00",
            ocaso_iso="2026-08-26T21:00:00",
            condicion=self.condicion,
            calidad_aire=self.calidad_aire
        )

        from unittest.mock import patch
        self.patcher_geoip = patch(
            "src.servicios.geocoding_service.GeocodingService.detectar_ubicacion_ip",
            return_value=self.ubicacion
        )
        self.patcher_cercanas = patch(
            "src.servicios.geocoding_service.GeocodingService.obtener_ciudades_cercanas",
            return_value=[self.ubicacion]
        )
        self.patcher_geoip.start()
        self.patcher_cercanas.start()

    def tearDown(self):
        self.patcher_geoip.stop()
        self.patcher_cercanas.stop()
        from PySide6.QtCore import QThreadPool
        QThreadPool.globalInstance().waitForDone(500)

    def test_calculo_astronomico_luna(self):
        # Luna nueva fija conocida
        dt_nueva = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        info_nueva = AstronomiaHelper.obtener_info_lunar(dt_nueva)
        self.assertEqual(info_nueva.nombre, "Luna Nueva")
        self.assertEqual(info_nueva.archivo_icono, "luna_nueva.png")
        self.assertLessEqual(info_nueva.iluminacion_pct, 5)

        # Luna actual
        info_actual = AstronomiaHelper.obtener_info_lunar()
        self.assertIn(".png", info_actual.archivo_icono)
        self.assertTrue((LUNA_DIR / info_actual.archivo_icono).exists())
        self.assertGreaterEqual(info_actual.iluminacion_pct, 0)
        self.assertLessEqual(info_actual.iluminacion_pct, 100)

    def test_calidad_aire_modelo(self):
        ca = DatosCalidadAire(aqi_europeo=15, aqi_us=35, pm2_5=5.0, pm10=10.0)
        self.assertEqual(ca.categoria, "Excelente")
        self.assertEqual(ca.color_hex, "#34d399")

        ca_alta = DatosCalidadAire(aqi_europeo=80, aqi_us=160, pm2_5=75.0, pm10=120.0)
        self.assertEqual(ca_alta.categoria, "Dañina")

    def test_tarjeta_fase_lunar(self):
        tarjeta = TarjetaFaseLunar()
        tarjeta.actualizar(self.actual)
        self.assertNotEqual(tarjeta.lbl_fase.text(), "")
        self.assertIn("Iluminación:", tarjeta.lbl_iluminacion.text())
        self.assertIn("Salida:", tarjeta.lbl_horarios.text())
        self.assertIn("Próx. luna llena:", tarjeta.lbl_proxima.text())

    def test_tarjeta_calidad_aire(self):
        tarjeta = TarjetaCalidadAire()
        tarjeta.actualizar(self.actual)
        self.assertEqual(tarjeta.lbl_aqi.text(), "42")
        self.assertEqual(tarjeta.badge_nivel.text(), "Excelente")
        self.assertIn("PM2.5: 6.8", tarjeta.lbl_particulas.text())

    def test_bento_grid_8_tarjetas(self):
        bento = BentoGridWidget()
        self.assertIsNotNone(bento.card_uv)
        self.assertIsNotNone(bento.card_viento)
        self.assertIsNotNone(bento.card_luna)
        self.assertIsNotNone(bento.card_sol)
        self.assertIsNotNone(bento.card_calidad_aire)
        self.assertIsNotNone(bento.card_humedad)
        self.assertIsNotNone(bento.card_visibilidad)
        self.assertIsNotNone(bento.card_presion)

        # Actualizar datos
        bento.actualizar_datos(self.actual)
        self.assertEqual(bento.card_calidad_aire.lbl_aqi.text(), "42")

    def test_curva_horaria_click_event(self):
        curva = CurvaHorariaWidget()
        horas = [
            PronosticoHora(
                fecha_hora_iso="2026-08-26T12:00:00",
                hora_etiqueta="12:00",
                temperatura=25.0,
                sensacion=25.0,
                probabilidad_lluvia=0,
                precipitacion_mm=0.0,
                condicion=self.condicion
            ),
            PronosticoHora(
                fecha_hora_iso="2026-08-26T13:00:00",
                hora_etiqueta="13:00",
                temperatura=26.0,
                sensacion=26.0,
                probabilidad_lluvia=20,
                precipitacion_mm=0.1,
                condicion=self.condicion
            )
        ]
        curva.set_datos(horas)
        self.assertEqual(curva.lienzo.selected_index, 0)
        self.assertIsNone(curva.lienzo.hover_index)

    def test_vista_ajustes_notificaciones(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigManager(Path(tmpdir) / "cfg.json")
            dialog = VistaAjustes(cfg)
            self.assertTrue(dialog.chk_notif_activadas.isChecked())
            self.assertTrue(dialog.chk_alerta_lluvia.isChecked())
            dialog.chk_alerta_atardecer.setChecked(True)
            dialog._guardar()

            notif = cfg.datos.get("notificaciones", {})
            self.assertTrue(notif.get("alerta_atardecer"))

    def test_banner_alerta_inundacion(self):
        from src.componentes.banner_alerta import BannerAlertaWidget
        banner = BannerAlertaWidget()
        # Simular día con lluvia torrencial (45 mm)
        dia_lluvioso = PronosticoDia(
            fecha_iso="2026-08-26",
            nombre_dia="Hoy",
            temp_min=18.0,
            temp_max=22.0,
            probabilidad_lluvia=95,
            precipitacion_total_mm=45.0,
            amanecer_iso="2026-08-26T07:00:00",
            ocaso_iso="2026-08-26T21:00:00",
            indice_uv_max=3.0,
            condicion=self.condicion
        )
        reporte_torrencial = ReporteClimaCompleto(
            ubicacion=self.ubicacion,
            actual=self.actual,
            horas_24h=[],
            dias_7d=[dia_lluvioso]
        )
        banner.actualizar_alerta(reporte_torrencial)
        self.assertFalse(banner.isHidden())
        self.assertIn("Inundación", banner.lbl_titulo.text())
        self.assertIn("45.0 mm", banner.lbl_desc.text())

    def test_banner_alerta_calor_extremo(self):
        from src.componentes.banner_alerta import BannerAlertaWidget
        banner = BannerAlertaWidget()
        dia_caluroso = PronosticoDia(
            fecha_iso="2026-08-26",
            nombre_dia="Hoy",
            temp_min=24.0,
            temp_max=41.5,
            probabilidad_lluvia=0,
            precipitacion_total_mm=0.0,
            amanecer_iso="2026-08-26T07:00:00",
            ocaso_iso="2026-08-26T21:00:00",
            indice_uv_max=10.0,
            condicion=self.condicion
        )
        reporte_calor = ReporteClimaCompleto(
            ubicacion=self.ubicacion,
            actual=self.actual,
            horas_24h=[],
            dias_7d=[dia_caluroso]
        )
        banner.actualizar_alerta(reporte_calor)
        self.assertFalse(banner.isHidden())
        self.assertIn("Calor Extremo", banner.lbl_titulo.text())
        self.assertIn("42°C", banner.lbl_desc.text())

    def test_pronostico_semanal_milimetros(self):
        from src.componentes.pronostico_semanal import PronosticoSemanalWidget
        semanal = PronosticoSemanalWidget()
        dias = [
            PronosticoDia(
                fecha_iso="2026-08-26",
                nombre_dia="Hoy",
                temp_min=18.0,
                temp_max=25.0,
                probabilidad_lluvia=80,
                precipitacion_total_mm=12.4,
                amanecer_iso="2026-08-26T07:00:00",
                ocaso_iso="2026-08-26T21:00:00",
                indice_uv_max=5.0,
                condicion=self.condicion
            )
        ]
        semanal.set_datos(dias, temp_actual=22.0)
        fila = semanal.filas_layout.itemAt(0).widget()
        self.assertIn("80%", fila.lbl_lluvia.text())
        self.assertIn("12.4mm", fila.lbl_lluvia.text())

    def test_gestor_instancia_unica(self):
        from src.utils.instancia_unica import GestorInstanciaUnica
        nombre_test_socket = "test_weatherapp_single_instance_ipc"
        g1 = GestorInstanciaUnica(nombre_socket=nombre_test_socket)
        self.assertFalse(g1.es_otra_instancia_activa())
        self.assertTrue(g1.iniciar_servidor())

        # Segunda instancia debe detectar a la primera
        g2 = GestorInstanciaUnica(nombre_socket=nombre_test_socket)
        self.assertTrue(g2.es_otra_instancia_activa())

        if g1.servidor:
            g1.servidor.close()


if __name__ == "__main__":
    unittest.main()



