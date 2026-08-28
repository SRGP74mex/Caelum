import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from config import (
    APP_NAME,
    ASSETS_DIR,
    BACKGROUNDS_DIR,
)
from src.componentes.bandeja_sistema import BandejaSistema
from src.componentes.banner_alerta import BannerAlertaWidget
from src.componentes.barra_busqueda import BarraBusqueda
from src.componentes.bento_grid import BentoGridWidget
from src.componentes.cabecera_clima import CabeceraClima
from src.componentes.curva_horaria import CurvaHorariaWidget
from src.componentes.fondo_particulas import FondoParticulasWidget
from src.componentes.pronostico_semanal import PronosticoSemanalWidget
from src.componentes.tarjeta_bento import TarjetaBento
from src.modelos.clima_datos import PronosticoDia, PronosticoHora, ReporteClimaCompleto, Ubicacion
from src.servicios.cache_manager import CacheManager
from src.servicios.config_manager import ConfigManager
from src.servicios.geocoding_service import GeocodingService
from src.servicios.i18n import establecer_idioma, t
from src.servicios.open_meteo_service import OpenMeteoService
from src.servicios.worker import ejecutar_en_segundo_plano
from src.utils.fecha_utils import FechaHelper
from src.utils.unidades import aplicar_preferencias_unidades, establecer_preferencias_unidades, sufijo_temperatura
from src.vistas.vista_ajustes import VistaAjustes

logger = logging.getLogger(__name__)

PALETAS_CIELO = {
    "dia_despejado": [QColor(24, 76, 120), QColor(48, 122, 178), QColor(95, 170, 222)],
    "dia_mayormente_despejado": [QColor(28, 80, 128), QColor(54, 128, 184), QColor(102, 175, 226)],
    "dia_parcialmente_despejado": [QColor(30, 85, 135), QColor(60, 135, 190), QColor(110, 180, 230)],
    "dia_parcialmente_nublado": [QColor(45, 65, 85), QColor(75, 105, 130), QColor(115, 145, 170)],
    "dia_nublado": [QColor(50, 60, 70), QColor(75, 90, 105), QColor(110, 125, 140)],
    "dia_cirrus": [QColor(35, 80, 130), QColor(70, 130, 185), QColor(120, 175, 225)],
    "dia_lluvia": [QColor(25, 35, 45), QColor(40, 55, 70), QColor(60, 78, 95)],
    "dia_neblina": [QColor(70, 80, 90), QColor(105, 115, 125), QColor(145, 155, 165)],
    "dia_banco_neblina": [QColor(65, 75, 85), QColor(98, 110, 120), QColor(135, 145, 155)],
    "dia_nevando": [QColor(60, 80, 100), QColor(95, 120, 145), QColor(140, 165, 190)],
    "dia_despejado_nevado": [QColor(50, 85, 130), QColor(90, 135, 180), QColor(150, 190, 225)],
    "dia_nevado_medio_nublado": [QColor(55, 75, 95), QColor(90, 115, 140), QColor(135, 160, 185)],
    "dia_nevado_nublado": [QColor(50, 65, 80), QColor(80, 100, 120), QColor(120, 140, 160)],
    "noche_despejado": [QColor(8, 14, 28), QColor(18, 28, 50), QColor(30, 44, 72)],
    "noche_mayormente_despejado": [QColor(9, 15, 29), QColor(19, 30, 52), QColor(32, 46, 74)],
    "noche_semidespejado": [QColor(10, 16, 30), QColor(20, 32, 54), QColor(34, 48, 76)],
    "noche_seminublado": [QColor(12, 18, 30), QColor(24, 34, 52), QColor(40, 52, 74)],
    "noche_nublado": [QColor(14, 20, 28), QColor(26, 35, 46), QColor(42, 52, 65)],
    "noche_cirrus": [QColor(10, 16, 32), QColor(22, 34, 58), QColor(38, 54, 82)],
    "noche_despejado_nevado": [QColor(12, 20, 38), QColor(25, 40, 68), QColor(48, 68, 100)],
    "amanecer": [QColor(75, 35, 65), QColor(145, 60, 75), QColor(230, 120, 70)],
    "atardecer": [QColor(65, 25, 55), QColor(135, 45, 65), QColor(215, 100, 60)]
}


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de WeatherApp Linux con fondos fotográficos panorámicos HD 16:9,
    motor de partículas a 60 FPS superpuesto, Bento Grid de 8 métricas y notificaciones inteligentes.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(560, 940)
        self.setMinimumSize(460, 700)

        # Icono oficial de ventana
        icon_path = ASSETS_DIR / "icons" / "weather_app.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Servicios
        self.meteo_service = OpenMeteoService()
        self.geocoding_service = GeocodingService()
        self.cache_manager = CacheManager()
        self.config_manager = ConfigManager()
        establecer_idioma(self.config_manager.datos.get("idioma", "auto"))
        establecer_preferencias_unidades(self.config_manager.datos.get("unidades", {}))

        # Registro de timestamps para control anti-spam de notificaciones
        self._ultimas_notificaciones: Dict[str, float] = {}

        # Fondos fotográficos en memoria
        self.fondos_pixmap: Dict[str, QPixmap] = {}
        self._cargar_fondos_fotograficos()

        # Caché del fondo escalado al tamaño actual de la ventana
        self._fondo_escalado_cache: Optional[QPixmap] = None
        self._fondo_escalado_cache_key: Optional[tuple] = None

        # Estado
        self.ubicacion_actual = self.config_manager.obtener_ultima_ciudad()
        self.reporte_actual: Optional[ReporteClimaCompleto] = None
        self.dia_activo: Optional[PronosticoDia] = None
        self.fondo_actual_key = "dia_despejado"
        self.colores_cielo: List[QColor] = PALETAS_CIELO["dia_despejado"]

        self._init_ui()
        self._init_tray()
        self._init_autorefresh()
        self._cargar_ubicacion_inicial()

    def _cargar_fondos_fotograficos(self) -> None:
        """Carga en memoria el conjunto de 20 imágenes panorámicas normalizadas."""
        mapeo_archivos = {
            "dia_despejado": "dia_despejado.png",
            "dia_mayormente_despejado": "dia_mayormente_despejado.png",
            "dia_parcialmente_despejado": "dia_parcialmente_despejado.png",
            "dia_parcialmente_nublado": "dia_parcialmente_despejado.png",
            "dia_nublado": "dia_nublado.png",
            "dia_cirrus": "dia_cirrus.png",
            "dia_lluvia": "dia_lluvia.png",
            "dia_neblina": "dia_neblina.png",
            "dia_banco_neblina": "dia_banco_neblina.png",
            "dia_nevando": "dia_nevando.png",
            "dia_despejado_nevado": "dia_despejado_nevado.png",
            "dia_nevado_medio_nublado": "dia_nevado_medio_nublado.png",
            "dia_nevado_nublado": "dia_nevado_nublado.png",
            "noche_despejado": "noche_despejado.png",
            "noche_mayormente_despejado": "noche_mayormente_despejado.png",
            "noche_semidespejado": "noche_semidespejado.png",
            "noche_seminublado": "noche_semidespejado.png",
            "noche_nublado": "noche_nublado.png",
            "noche_cirrus": "noche_cirrus.png",
            "noche_despejado_nevado": "noche_despejado_nevado.png",
            "amanecer": "amanecer.png",
            "atardecer": "atardecer.png",
        }
        for key, fname in mapeo_archivos.items():
            path = BACKGROUNDS_DIR / fname
            if path.exists():
                pix = QPixmap(str(path))
                if not pix.isNull():
                    self.fondos_pixmap[key] = pix

    def _init_ui(self) -> None:
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Motor de partículas de fondo
        self.fondo_particulas = FondoParticulasWidget(self.central_widget)
        self.fondo_particulas.lower()

        root_layout = QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        # 1. Barra Superior
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(10)

        self.barra_busqueda = BarraBusqueda(self)
        self.barra_busqueda.ciudad_seleccionada.connect(self.cambiar_ciudad)
        top_bar_layout.addWidget(self.barra_busqueda, stretch=1)

        self.btn_refrescar = QPushButton("🔄", self)
        self.btn_refrescar.setFixedSize(38, 38)
        self.btn_refrescar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refrescar.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.30);
                border-radius: 12px;
                font-size: 16px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.28);
                border: 1px solid rgba(255, 255, 255, 0.45);
            }
        """)
        self.btn_refrescar.clicked.connect(self.refrescar_clima)
        top_bar_layout.addWidget(self.btn_refrescar)

        self.btn_ajustes = QPushButton("⚙️", self)
        self.btn_ajustes.setFixedSize(38, 38)
        self.btn_ajustes.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ajustes.setStyleSheet(self.btn_refrescar.styleSheet())
        self.btn_ajustes.clicked.connect(self._abrir_ajustes)
        top_bar_layout.addWidget(self.btn_ajustes)

        root_layout.addLayout(top_bar_layout)

        # 2. Área de desplazamiento
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(4, 8, 4, 16)
        self.scroll_layout.setSpacing(16)

        # Banner de Alertas Meteorológicas Críticas
        self.banner_alerta = BannerAlertaWidget(self.scroll_content)
        self.scroll_layout.addWidget(self.banner_alerta)

        # Cabecera Principal
        self.cabecera = CabeceraClima(self.scroll_content)
        self.cabecera.establecer_config_calendarios(self.config_manager.obtener_calendarios_activos())
        self.scroll_layout.addWidget(self.cabecera)

        # Tarjeta de Pronóstico 24 Horas con Curva Bézier
        self.tarjeta_horas = TarjetaBento(t("pronostico.titulo_horas"), "⏱️", self.scroll_content)

        self.lbl_detalle_hora = QLabel("", self.tarjeta_horas)
        self.lbl_detalle_hora.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.85); margin-top: -4px;")
        self.tarjeta_horas.agregar_contenido(self.lbl_detalle_hora)

        self.curva_horaria = CurvaHorariaWidget(self.tarjeta_horas)
        self.curva_horaria.hora_seleccionada.connect(self._on_hora_seleccionada)
        self.tarjeta_horas.agregar_contenido(self.curva_horaria)
        self.scroll_layout.addWidget(self.tarjeta_horas)

        # Tarjeta de Pronóstico 7 Días con Selección por Clic
        self.pronostico_semanal = PronosticoSemanalWidget(self.scroll_content)
        self.pronostico_semanal.dia_seleccionado.connect(self._on_dia_seleccionado)
        self.scroll_layout.addWidget(self.pronostico_semanal)

        # Bento Grid de 8 Tarjetas de Métricas
        self.bento_grid = BentoGridWidget(self.scroll_content)
        self.scroll_layout.addWidget(self.bento_grid)

        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.scroll_area)

    def _init_tray(self) -> None:
        self.bandeja = BandejaSistema(self)
        self.bandeja.solicitar_mostrar_ocultar.connect(self.toggle_visibilidad)
        self.bandeja.solicitar_refresco.connect(self.refrescar_clima)
        self.bandeja.solicitar_salir.connect(QApplication.instance().quit)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.bandeja.show()

    def _init_autorefresh(self) -> None:
        """Configura un temporizador para refrescar los datos automáticamente cada 15 minutos."""
        self.timer_autorefresh = QTimer(self)
        self.timer_autorefresh.setInterval(15 * 60 * 1000)
        self.timer_autorefresh.timeout.connect(self.refrescar_clima)
        self.timer_autorefresh.start()

    def restaurar_y_enfocar(self) -> None:
        """Restaura la ventana si estaba oculta/minimizada y la pone en primer plano con foco activo."""
        if not self.isVisible():
            self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def toggle_visibilidad(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.restaurar_y_enfocar()

    def _abrir_ajustes(self) -> None:
        dialogo = VistaAjustes(self.config_manager, parent=self)
        dialogo.ajustes_guardados.connect(self._aplicar_ajustes_actuales)
        dialogo.exec()

    def _aplicar_ajustes_actuales(self) -> None:
        """Se ejecuta al guardar ajustes: aplica unidades e idioma y refresca sin consultar la red."""
        from src.servicios.i18n import t
        establecer_idioma(self.config_manager.datos.get("idioma", "auto"))
        establecer_preferencias_unidades(self.config_manager.datos.get("unidades", {}))
        self.cabecera.establecer_config_calendarios(self.config_manager.obtener_calendarios_activos())

        self.tarjeta_horas.lbl_titulo.setText(t("pronostico.titulo_horas"))
        self.pronostico_semanal.lbl_titulo.setText(t("pronostico.titulo_semanal"))
        self.barra_busqueda.input_busqueda.setPlaceholderText(t("busqueda.placeholder"))

        if self.config_manager.datos.get("mostrar_bandeja", True) and QSystemTrayIcon.isSystemTrayAvailable():
            self.bandeja.show()
        else:
            self.bandeja.hide()

        if self.ubicacion_actual:
            reporte_crudo = self.cache_manager.obtener_reporte(
                self.ubicacion_actual.latitud, self.ubicacion_actual.longitud, ignorar_ttl=True
            )
            if reporte_crudo:
                self._aplicar_reporte(reporte_crudo)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.config_manager.datos.get("cerrar_a_bandeja") and hasattr(self, "bandeja") and self.bandeja.isVisible():
            event.ignore()
            self.hide()
        else:
            if hasattr(self, "bandeja"):
                self.bandeja.hide()
            event.accept()
            QApplication.instance().quit()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "fondo_particulas"):
            self.fondo_particulas.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # 1. Dibujar fotografía atmosférica panorámica escalada
        pixmap = self.fondos_pixmap.get(self.fondo_actual_key)
        if pixmap and not pixmap.isNull():
            cache_key = (self.fondo_actual_key, w, h)
            if cache_key != self._fondo_escalado_cache_key:
                self._fondo_escalado_cache = pixmap.scaled(
                    w, h,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._fondo_escalado_cache_key = cache_key

            scaled_pix = self._fondo_escalado_cache
            x_offset = (scaled_pix.width() - w) // 2
            y_offset = (scaled_pix.height() - h) // 2
            painter.drawPixmap(0, 0, scaled_pix, x_offset, y_offset, w, h)
        else:
            # Fallback a degradado suave
            gradiente = QLinearGradient(0, 0, 0, h)
            if len(self.colores_cielo) >= 3:
                gradiente.setColorAt(0.0, self.colores_cielo[0])
                gradiente.setColorAt(0.5, self.colores_cielo[1])
                gradiente.setColorAt(1.0, self.colores_cielo[2])
            else:
                gradiente.setColorAt(0.0, self.colores_cielo[0])
                gradiente.setColorAt(1.0, self.colores_cielo[-1])
            painter.fillRect(self.rect(), gradiente)

        # 2. Viñeta Glassmorphism para contraste óptimo de textos y tarjetas
        vignette = QLinearGradient(0, 0, 0, h)
        vignette.setColorAt(0.0, QColor(10, 15, 25, 110))
        vignette.setColorAt(0.25, QColor(10, 15, 25, 50))
        vignette.setColorAt(0.65, QColor(10, 15, 25, 65))
        vignette.setColorAt(1.0, QColor(10, 15, 25, 145))
        painter.fillRect(self.rect(), vignette)

    def _on_dia_seleccionado(self, dia: PronosticoDia) -> None:
        """Actualiza la interfaz al hacer clic sobre un día de la semana."""
        if not self.reporte_actual:
            return

        self.dia_activo = dia
        es_hoy = (dia.nombre_dia == "Hoy")

        if dia.horas:
            self.curva_horaria.set_datos(dia.horas)
        else:
            self.curva_horaria.set_datos(self.reporte_actual.horas_24h)

        if es_hoy:
            self.cabecera.actualizar_datos(self.reporte_actual)
            self.bento_grid.actualizar_datos(self.reporte_actual.actual)
            self._actualizar_paleta_cielo(
                self.reporte_actual.actual.condicion.animacion_tipo,
                self.reporte_actual.actual.condicion.es_dia,
                wmo_code=self.reporte_actual.actual.condicion.wmo_code,
                precipitacion_mm=self.reporte_actual.actual.precipitacion_mm,
                viento_velocidad=self.reporte_actual.actual.viento_velocidad,
                amanecer_iso=self.reporte_actual.actual.amanecer_iso,
                ocaso_iso=self.reporte_actual.actual.ocaso_iso
            )
        else:
            self.cabecera.lbl_ciudad.setText(self.ubicacion_actual.ciudad)
            region_str = f"{self.ubicacion_actual.admin1}, " if self.ubicacion_actual.admin1 and self.ubicacion_actual.admin1 != self.ubicacion_actual.ciudad else ""
            self.cabecera.lbl_pais.setText(f"{region_str}{self.ubicacion_actual.pais}")
            self.cabecera.lbl_temperatura.setText(f"{round(dia.temp_max)}°")
            self.cabecera.lbl_condicion.setText(f"{dia.condicion.descripcion} • {dia.nombre_dia}")
            self.cabecera.lbl_rango_hoy.setText(f"Máx: {round(dia.temp_max)}°  •  Mín: {round(dia.temp_min)}°")

            try:
                dt = FechaHelper.parse_iso(dia.fecha_iso)
                self.cabecera.actualizar_fechas(dt)
            except Exception:
                pass

            self.bento_grid.actualizar_por_dia(dia)
            self._actualizar_paleta_cielo(
                dia.condicion.animacion_tipo,
                es_dia=True,
                wmo_code=dia.condicion.wmo_code,
                precipitacion_mm=dia.precipitacion_total_mm,
                amanecer_iso=dia.amanecer_iso,
                ocaso_iso=dia.ocaso_iso
            )

        precip_info = f" • 🌧️ {dia.precipitacion_total_mm:.1f} mm esperados" if dia.precipitacion_total_mm > 0 else ""
        self.lbl_detalle_hora.setText(f"Mostrando pronóstico para {dia.nombre_dia} ({dia.condicion.descripcion}){precip_info}")
        self.update()

    def _on_hora_seleccionada(self, hora_obj: Optional[PronosticoHora]) -> None:
        """Actualiza la interfaz al hacer clic sobre una hora específica de la curva."""
        if not self.reporte_actual or not hora_obj:
            return

        prob_str = ""
        if hora_obj.probabilidad_lluvia > 0 or hora_obj.precipitacion_mm > 0:
            mm_str = f" ({hora_obj.precipitacion_mm:.1f} mm/h)" if hora_obj.precipitacion_mm > 0 else ""
            prob_str = f" • 🌧️ {hora_obj.probabilidad_lluvia}%{mm_str}"

        uv_str = f" • UV: {hora_obj.indice_uv:.0f}" if hora_obj.indice_uv > 0 else ""
        self.lbl_detalle_hora.setText(
            f"🕒 {hora_obj.hora_etiqueta}: {hora_obj.condicion.descripcion} • Sensación: {hora_obj.sensacion:.1f}{sufijo_temperatura()}{prob_str}{uv_str}"
        )

        self.cabecera.lbl_temperatura.setText(f"{round(hora_obj.temperatura)}°")
        dia_ref = f" • {self.dia_activo.nombre_dia}" if self.dia_activo and self.dia_activo.nombre_dia != "Hoy" else ""
        self.cabecera.lbl_condicion.setText(f"{hora_obj.condicion.descripcion} ({hora_obj.hora_etiqueta}{dia_ref})")

        am_iso = self.reporte_actual.actual.amanecer_iso
        oc_iso = self.reporte_actual.actual.ocaso_iso
        self.bento_grid.actualizar_por_hora(hora_obj, amanecer_iso=am_iso, ocaso_iso=oc_iso)

        self._actualizar_paleta_cielo(
            hora_obj.condicion.animacion_tipo,
            not hora_obj.es_noche,
            wmo_code=hora_obj.condicion.wmo_code,
            precipitacion_mm=hora_obj.precipitacion_mm,
            viento_velocidad=hora_obj.viento_velocidad,
            amanecer_iso=am_iso,
            ocaso_iso=oc_iso
        )
        self.update()

    def _cargar_ubicacion_inicial(self) -> None:
        if self.ubicacion_actual:
            self._consultar_clima(self.ubicacion_actual)
        else:
            def _detectar():
                return self.geocoding_service.detectar_ubicacion_ip()

            def _on_detectada(ub: Ubicacion):
                self.ubicacion_actual = ub
                self.config_manager.guardar_ultima_ciudad(ub)
                self._consultar_clima(ub)

            ejecutar_en_segundo_plano(_detectar, on_result=_on_detectada)

    def cambiar_ciudad(self, ubicacion: Ubicacion) -> None:
        self.ubicacion_actual = ubicacion
        self.dia_activo = None
        self.config_manager.guardar_ultima_ciudad(ubicacion)

        self.cabecera.lbl_ciudad.setText(ubicacion.ciudad)
        region_str = f"{ubicacion.admin1}, " if ubicacion.admin1 and ubicacion.admin1 != ubicacion.ciudad else ""
        self.cabecera.lbl_pais.setText(f"{region_str}{ubicacion.pais}")
        self.cabecera.lbl_condicion.setText("Cargando pronóstico meteorológico...")
        self.lbl_detalle_hora.setText(f"Consultando datos para {ubicacion.ciudad}...")

        self._consultar_clima(ubicacion)

    def refrescar_clima(self) -> None:
        if self.ubicacion_actual:
            self.cabecera.lbl_condicion.setText("Actualizando datos en vivo...")
            self._consultar_clima(self.ubicacion_actual, ignorar_cache=True)

    def _consultar_clima(self, ubicacion: Ubicacion, ignorar_cache: bool = False) -> None:
        if not ignorar_cache:
            reporte_cache = self.cache_manager.obtener_reporte(ubicacion.latitud, ubicacion.longitud)
            if reporte_cache:
                self._aplicar_reporte(reporte_cache)
                return

        def _fetch():
            return self.meteo_service.obtener_reporte_completo(ubicacion)

        def _on_result(reporte: ReporteClimaCompleto):
            self.cache_manager.guardar_reporte(reporte)
            self._aplicar_reporte(reporte)

        def _on_error(err: str):
            logger.warning("Error al consultar clima para %s: %s", ubicacion.ciudad, err)
            self.cabecera.lbl_condicion.setText("⚠️ Error al actualizar")
            self.lbl_detalle_hora.setText(f"{err} — pulsa 🔄 para reintentar")

        ejecutar_en_segundo_plano(_fetch, on_result=_on_result, on_error=_on_error)

    def _aplicar_reporte(self, reporte: ReporteClimaCompleto) -> None:
        try:
            reporte = aplicar_preferencias_unidades(reporte)
            self.reporte_actual = reporte
            self.dia_activo = reporte.dias_7d[0] if reporte.dias_7d else None

            # Actualizar Banner de Alertas Meteorológicas Críticas
            if hasattr(self, "banner_alerta"):
                self.banner_alerta.actualizar_alerta(reporte)

            self.cabecera.actualizar_datos(reporte)
            self.curva_horaria.set_datos(reporte.horas_24h)
            self.pronostico_semanal.set_datos(reporte.dias_7d, temp_actual=reporte.actual.temperatura)
            self.bento_grid.actualizar_datos(reporte.actual)
            self._actualizar_paleta_cielo(
                reporte.actual.condicion.animacion_tipo,
                reporte.actual.condicion.es_dia,
                wmo_code=reporte.actual.condicion.wmo_code,
                precipitacion_mm=reporte.actual.precipitacion_mm,
                viento_velocidad=reporte.actual.viento_velocidad,
                amanecer_iso=reporte.actual.amanecer_iso,
                ocaso_iso=reporte.actual.ocaso_iso
            )
            self.lbl_detalle_hora.setText("Haz clic sobre cualquier hora o día para ver el pronóstico detallado")

            if hasattr(self, "bandeja"):
                self.bandeja.actualizar_clima_tray(reporte)

            self._evaluar_notificaciones(reporte)
            self.update()
        except Exception as e:
            logger.error("Error visual al aplicar reporte: %s", e, exc_info=True)
            self.cabecera.lbl_condicion.setText(f"⚠️ Error visual: {e}")

    def _actualizar_paleta_cielo(
        self,
        anim_tipo: str,
        es_dia: bool = True,
        wmo_code: int = 0,
        precipitacion_mm: float = 0.0,
        viento_velocidad: float = 0.0,
        amanecer_iso: str = "",
        ocaso_iso: str = ""
    ) -> None:
        # 1. Actualizar motor de partículas modulado por lluvia/viento
        if hasattr(self, "fondo_particulas"):
            self.fondo_particulas.set_modo_clima(anim_tipo, es_dia)

        # 2. Detección de ventana solar (Amanecer / Atardecer)
        key = "dia_despejado" if es_dia else "noche_despejado"
        es_ventana_solar = False

        if amanecer_iso or ocaso_iso:
            try:
                ahora = datetime.now(timezone.utc)
                if amanecer_iso:
                    am_dt = FechaHelper.parse_iso(amanecer_iso)
                    if abs((ahora - am_dt).total_seconds()) <= 2400:  # +- 40 min
                        key = "amanecer"
                        es_ventana_solar = True
                if not es_ventana_solar and ocaso_iso:
                    oc_dt = FechaHelper.parse_iso(ocaso_iso)
                    if abs((ahora - oc_dt).total_seconds()) <= 2400:  # +- 40 min
                        key = "atardecer"
                        es_ventana_solar = True
            except Exception:
                pass

        if not es_ventana_solar:
            # Evaluar por WMO y condiciones climáticas
            if wmo_code in [71, 73, 75, 77, 85, 86] or anim_tipo == "snow":
                if es_dia:
                    if wmo_code in [73, 75, 86] or precipitacion_mm >= 1.0:
                        key = "dia_nevando"
                    elif wmo_code == 71:
                        key = "dia_despejado_nevado"
                    else:
                        key = "dia_nevado_medio_nublado"
                else:
                    key = "noche_despejado_nevado"
            elif wmo_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99] or anim_tipo in ["rain", "thunderstorm"]:
                key = "dia_lluvia" if es_dia else "noche_nublado"
            elif wmo_code in [45, 48] or anim_tipo == "fog":
                key = "dia_banco_neblina" if es_dia else "noche_nublado"
            elif wmo_code == 2:
                key = "dia_parcialmente_despejado" if es_dia else "noche_semidespejado"
            elif wmo_code == 1:
                key = "dia_mayormente_despejado" if es_dia else "noche_mayormente_despejado"
            elif wmo_code == 3 or anim_tipo == "clouds":
                key = "dia_nublado" if es_dia else "noche_nublado"
            else:
                key = "dia_despejado" if es_dia else "noche_despejado"

        # Asignar fondo o fallback si no está cargado
        self.fondo_actual_key = key if key in self.fondos_pixmap else ("dia_despejado" if es_dia else "noche_despejado")
        self.colores_cielo = PALETAS_CIELO.get(
            self.fondo_actual_key,
            PALETAS_CIELO["dia_despejado" if es_dia else "noche_despejado"]
        )
        self.update()

    def _evaluar_notificaciones(self, reporte: ReporteClimaCompleto) -> None:
        """Motor inteligente de notificaciones y alertas preventivas del sistema."""
        if not hasattr(self, "bandeja"):
            return

        notif_cfg = self.config_manager.datos.get("notificaciones", {})
        if not notif_cfg.get("activadas", True):
            return

        ahora_ts = time.time()
        act = reporte.actual

        # 1. Alerta de Lluvia Torrencial / Riesgo de Inundación
        precip_hoy = reporte.dias_7d[0].precipitacion_total_mm if reporte.dias_7d else act.precipitacion_mm
        max_precip_h = max((h.precipitacion_mm for h in reporte.horas_24h[:6]), default=0.0) if reporte.horas_24h else 0.0

        if notif_cfg.get("alerta_tormenta", True) and (precip_hoy >= 30.0 or max_precip_h >= 12.0):
            ult_inund = self._ultimas_notificaciones.get("inundacion", 0)
            if ahora_ts - ult_inund > 14400:  # Cooldown 4 horas
                self.bandeja.mostrar_alerta(
                    "🌊 Alerta de Lluvia Torrencial / Inundación",
                    f"Se pronostican hasta {precip_hoy:.1f} mm en {reporte.ubicacion.ciudad}. Riesgo de inundación y acumulación de agua.",
                    icon_tipo="critical"
                )
                self._ultimas_notificaciones["inundacion"] = ahora_ts

        # 2. Alerta de Ola de Calor Extremo
        temp_max_hoy = reporte.dias_7d[0].temp_max if reporte.dias_7d else act.temp_max_hoy
        if notif_cfg.get("alerta_tormenta", True) and (temp_max_hoy >= 38.0 or act.sensacion_termica >= 40.0):
            ult_calor = self._ultimas_notificaciones.get("calor", 0)
            if ahora_ts - ult_calor > 21600:  # Cooldown 6 horas
                self.bandeja.mostrar_alerta(
                    "🔥 Alerta de Calor Extremo",
                    f"Temperatura máxima alcanzará los {round(temp_max_hoy)}°C (Sensación {round(act.sensacion_termica)}°C) en {reporte.ubicacion.ciudad}. Hidrátate bien.",
                    icon_tipo="warning"
                )
                self._ultimas_notificaciones["calor"] = ahora_ts

        # 3. Alerta de lluvia inminente en las próximas 2 horas
        if notif_cfg.get("alerta_lluvia", True):
            ult_lluvia = self._ultimas_notificaciones.get("lluvia", 0)
            if ahora_ts - ult_lluvia > 7200:  # Cooldown 2 horas
                for h in reporte.horas_24h[1:3]:
                    if (h.probabilidad_lluvia >= 60 or h.precipitacion_mm >= 0.5) and act.precipitacion_mm == 0:
                        mm_str = f" ({h.precipitacion_mm:.1f} mm)" if h.precipitacion_mm > 0 else ""
                        self.bandeja.mostrar_alerta(
                            "🌧️ Se espera lluvia pronto",
                            f"Se pronostica lluvia a las {h.hora_etiqueta} ({h.probabilidad_lluvia}% prob.{mm_str}) en {reporte.ubicacion.ciudad}."
                        )
                        self._ultimas_notificaciones["lluvia"] = ahora_ts
                        break

        # 4. Alerta de tormenta o clima severo
        if notif_cfg.get("alerta_tormenta", True):
            ult_severo = self._ultimas_notificaciones.get("severo", 0)
            if ahora_ts - ult_severo > 10800:  # Cooldown 3 horas
                if act.condicion.wmo_code in [95, 96, 99]:
                    granizo_str = " con posible granizo" if act.condicion.wmo_code in [96, 99] else ""
                    self.bandeja.mostrar_alerta(
                        "⚡ Alerta de Tormenta",
                        f"Actividad de tormenta eléctrica{granizo_str} registrada en {reporte.ubicacion.ciudad}.",
                        icon_tipo="warning"
                    )
                    self._ultimas_notificaciones["severo"] = ahora_ts
                elif act.viento_rafagas and act.viento_rafagas >= 60.0:
                    self.bandeja.mostrar_alerta(
                        "💨 Viento Fuerte",
                        f"Ráfagas de viento de {round(act.viento_rafagas)} km/h en {reporte.ubicacion.ciudad}.",
                        icon_tipo="warning"
                    )
                    self._ultimas_notificaciones["severo"] = ahora_ts

        # 5. Aviso de atardecer
        if notif_cfg.get("alerta_atardecer", False):
            ult_ocaso = self._ultimas_notificaciones.get("atardecer", 0)
            if ahora_ts - ult_ocaso > 43200 and act.ocaso_iso:  # Cooldown 12 horas
                try:
                    ocaso_dt = FechaHelper.parse_iso(act.ocaso_iso)
                    ahora_dt = datetime.now(timezone.utc)
                    minutos_restantes = (ocaso_dt - ahora_dt).total_seconds() / 60.0
                    if 10 <= minutos_restantes <= 25:
                        oc_str = FechaHelper.formato_hora_corta(act.ocaso_iso)
                        self.bandeja.mostrar_alerta(
                            "🌅 Atardecer en curso",
                            f"El sol se ocultará a las {oc_str} en {reporte.ubicacion.ciudad}."
                        )
                        self._ultimas_notificaciones["atardecer"] = ahora_ts
                except Exception:
                    pass

