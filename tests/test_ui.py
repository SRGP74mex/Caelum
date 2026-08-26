import unittest
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Configurar QPA headless para pruebas
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from src.modelos.clima_datos import (
    Ubicacion,
    CondicionClimatica,
    ClimaActual,
    PronosticoHora,
    PronosticoDia,
    ReporteClimaCompleto,
)
from src.componentes.tarjeta_bento import TarjetaBento
from src.componentes.cabecera_clima import CabeceraClima
from src.componentes.barra_busqueda import BarraBusqueda
from src.componentes.curva_horaria import CurvaHorariaWidget, LienzoCurvaHoraria
from src.componentes.fondo_particulas import FondoParticulasWidget
from src.componentes.pronostico_semanal import PronosticoSemanalWidget, BarraRangoTermico
from src.componentes.bento_grid import BentoGridWidget
from src.componentes.tarjetas_metricas import BrujulaWidget, ArcoSolarWidget
from src.componentes.bandeja_sistema import BandejaSistema
from src.servicios.config_manager import ConfigManager
from src.vistas.ventana_principal import VentanaPrincipal

class TestUIComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.ubicacion = Ubicacion(
            ciudad="Sevilla",
            pais="España",
            latitud=37.3891,
            longitud=-5.9845,
            timezone="Europe/Madrid",
            admin1="Andalucía"
        )
        self.condicion = CondicionClimatica(
            wmo_code=0,
            descripcion="Despejado",
            icon_name="clear-day",
            es_dia=True,
            animacion_tipo="clear"
        )
        self.actual = ClimaActual(
            temperatura=28.4,
            sensacion_termica=29.1,
            temp_max_hoy=32.0,
            temp_min_hoy=19.0,
            humedad_relativa=45,
            punto_rocio=14.0,
            viento_velocidad=12.0,
            viento_direccion=220,
            viento_rafagas=18.0,
            indice_uv=8.5,
            presion_hpa=1014.0,
            visibilidad_km=10.0,
            probabilidad_lluvia=0,
            precipitacion_mm=0.0,
            amanecer_iso="2026-08-25T07:40:00",
            ocaso_iso="2026-08-25T21:10:00",
            condicion=self.condicion
        )
        self.reporte = ReporteClimaCompleto(
            ubicacion=self.ubicacion,
            actual=self.actual,
            horas_24h=[],
            dias_7d=[]
        )

    def tearDown(self):
        from PySide6.QtCore import QThreadPool
        QThreadPool.globalInstance().waitForDone(200)

    def test_tarjeta_bento_creacion(self):
        tarjeta = TarjetaBento(titulo="Índice UV", icono="☀️")
        self.assertEqual(tarjeta.lbl_titulo.text(), "ÍNDICE UV")
        self.assertEqual(tarjeta.lbl_icono.text(), "☀️")

    def test_cabecera_actualizar_datos(self):
        cabecera = CabeceraClima()
        cabecera.actualizar_datos(self.reporte)

        self.assertEqual(cabecera.lbl_ciudad.text(), "Sevilla")
        self.assertIn("Andalucía, España", cabecera.lbl_pais.text())
        self.assertEqual(cabecera.lbl_temperatura.text(), "28°")
        self.assertEqual(cabecera.lbl_condicion.text(), "Despejado")
        self.assertIn("32°", cabecera.lbl_rango_hoy.text())
        self.assertIn("19°", cabecera.lbl_rango_hoy.text())

    def test_barra_busqueda_senales(self):
        barra = BarraBusqueda()
        barra.show()
        ciudades_recibidas = []
        barra.ciudad_seleccionada.connect(lambda ub: ciudades_recibidas.append(ub))

        # Simular selección de ciudad
        barra._mostrar_sugerencias([self.ubicacion])
        self.assertFalse(barra.lista_sugerencias.isHidden())
        self.assertEqual(barra.lista_sugerencias.count(), 1)

        item = barra.lista_sugerencias.item(0)
        barra._on_item_clicked(item)

        self.assertEqual(len(ciudades_recibidas), 1)
        self.assertEqual(ciudades_recibidas[0].ciudad, "Sevilla")
        self.assertTrue(barra.lista_sugerencias.isHidden())

    def test_ventana_principal_creacion(self):
        ventana = VentanaPrincipal()
        self.assertIsNotNone(ventana.cabecera)
        self.assertIsNotNone(ventana.barra_busqueda)
        self.assertIsNotNone(ventana.curva_horaria)
        self.assertIsNotNone(ventana.fondo_particulas)
        self.assertEqual(ventana.windowTitle(), "WeatherApp Linux")

    def test_curva_horaria_render(self):
        curva = CurvaHorariaWidget()
        horas = [
            PronosticoHora(
                fecha_hora_iso="2026-08-25T18:00:00",
                hora_etiqueta="Ahora",
                temperatura=28.0,
                sensacion=29.0,
                probabilidad_lluvia=10,
                precipitacion_mm=0.0,
                condicion=self.condicion
            ),
            PronosticoHora(
                fecha_hora_iso="2026-08-25T19:00:00",
                hora_etiqueta="19:00",
                temperatura=26.5,
                sensacion=27.0,
                probabilidad_lluvia=30,
                precipitacion_mm=0.2,
                condicion=self.condicion
            )
        ]
        curva.set_datos(horas)
        self.assertEqual(len(curva.lienzo.horas), 2)
        self.assertEqual(curva.lienzo.width(), 2 * curva.lienzo.col_width)

    def test_fondo_particulas_animacion(self):
        fondo = FondoParticulasWidget()
        fondo.resize(400, 600)
        fondo.set_modo_clima("rain", es_dia=True)
        self.assertEqual(fondo.modo_clima, "rain")
        self.assertGreater(len(fondo.gotas), 0)

        fondo.set_modo_clima("snow", es_dia=False)
        self.assertEqual(fondo.modo_clima, "snow")
        self.assertGreater(len(fondo.copos), 0)

        fondo.set_modo_clima("clear", es_dia=False)
        self.assertEqual(fondo.modo_clima, "clear_night")
        self.assertGreater(len(fondo.estrellas), 0)

    def test_pronostico_semanal_render(self):
        semanal = PronosticoSemanalWidget()
        dias = [
            PronosticoDia(
                fecha_iso="2026-08-25",
                nombre_dia="Hoy",
                temp_min=18.0,
                temp_max=32.0,
                probabilidad_lluvia=10,
                precipitacion_total_mm=0.0,
                amanecer_iso="2026-08-25T07:00:00",
                ocaso_iso="2026-08-25T21:00:00",
                indice_uv_max=8.0,
                condicion=self.condicion
            ),
            PronosticoDia(
                fecha_iso="2026-08-26",
                nombre_dia="Mié",
                temp_min=19.0,
                temp_max=30.0,
                probabilidad_lluvia=40,
                precipitacion_total_mm=1.2,
                amanecer_iso="2026-08-26T07:01:00",
                ocaso_iso="2026-08-26T20:59:00",
                indice_uv_max=7.0,
                condicion=self.condicion
            )
        ]
        semanal.set_datos(dias, temp_actual=28.0)
        self.assertEqual(semanal.filas_layout.count(), 2)

    def test_bento_grid_actualizar(self):
        bento = BentoGridWidget()
        bento.actualizar_datos(self.actual)
        self.assertEqual(bento.card_uv.lbl_valor.text(), "8")
        self.assertIn("12 km/h", bento.card_viento.lbl_velocidad.text())
        self.assertIn("45%", bento.card_humedad.lbl_valor.text())
        self.assertIn("1014 hPa", bento.card_presion.lbl_valor.text())
        self.assertIn("10.0 km", bento.card_visibilidad.lbl_valor.text())

    def test_brujula_y_arco_solar(self):
        brujula = BrujulaWidget()
        brujula.set_direccion(180)
        self.assertEqual(brujula.grados, 180)

        arco = ArcoSolarWidget()
        arco.set_tiempos("2026-08-25T06:00:00", "2026-08-25T20:00:00")
        self.assertGreaterEqual(arco.progreso_solar, 0.0)
        self.assertLessEqual(arco.progreso_solar, 1.0)

    def test_config_manager(self):
        import tempfile
        from pathlib import Path
        temp_dir = Path(tempfile.mkdtemp())
        cfg_file = temp_dir / "config.json"

        cfg = ConfigManager(ruta_archivo=cfg_file)
        cfg.guardar_ultima_ciudad(self.ubicacion)

        ub_recuperada = cfg.obtener_ultima_ciudad()
        self.assertEqual(ub_recuperada.ciudad, "Sevilla")
        self.assertEqual(ub_recuperada.pais, "España")

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_bandeja_sistema(self):
        bandeja = BandejaSistema()
        self.assertIsNotNone(bandeja.icon())
        self.assertIsNotNone(bandeja.contextMenu())
        bandeja.actualizar_clima_tray(self.reporte)
        self.assertIn("Sevilla", bandeja.toolTip())

if __name__ == "__main__":
    unittest.main()
