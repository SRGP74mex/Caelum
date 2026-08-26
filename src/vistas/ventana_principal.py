from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QLabel, QFrame, QSizePolicy,
    QApplication, QSystemTrayIcon
)
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import (
    QPainter, QLinearGradient, QColor, QPaintEvent, QResizeEvent,
    QIcon, QPixmap
)

from typing import Optional, List, Dict
from pathlib import Path
from config import (
    APP_NAME, ASSETS_DIR, BACKGROUNDS_DIR, DEFAULT_CITY, DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE, DEFAULT_TIMEZONE
)
from src.modelos.clima_datos import Ubicacion, ReporteClimaCompleto, PronosticoHora, PronosticoDia
from src.servicios.open_meteo_service import OpenMeteoService
from src.servicios.geocoding_service import GeocodingService
from src.servicios.cache_manager import CacheManager
from src.servicios.config_manager import ConfigManager
from src.servicios.worker import ejecutar_en_segundo_plano
from src.utils.fecha_utils import FechaHelper
from src.componentes.cabecera_clima import CabeceraClima
from src.componentes.barra_busqueda import BarraBusqueda
from src.componentes.tarjeta_bento import TarjetaBento
from src.componentes.curva_horaria import CurvaHorariaWidget
from src.componentes.fondo_particulas import FondoParticulasWidget
from src.componentes.pronostico_semanal import PronosticoSemanalWidget
from src.componentes.bento_grid import BentoGridWidget
from src.componentes.bandeja_sistema import BandejaSistema

PALETAS_CIELO = {
    "clear_day": [QColor(24, 76, 120), QColor(48, 122, 178), QColor(95, 170, 222)],
    "clear_night": [QColor(10, 16, 32), QColor(22, 34, 58), QColor(36, 52, 84)],
    "clouds_day": [QColor(55, 71, 79), QColor(84, 110, 122), QColor(120, 144, 156)],
    "clouds_night": [QColor(20, 28, 36), QColor(38, 50, 60), QColor(55, 71, 79)],
    "rain": [QColor(30, 38, 48), QColor(45, 58, 72), QColor(62, 80, 98)],
    "snow": [QColor(70, 90, 110), QColor(115, 135, 155), QColor(170, 190, 210)],
    "thunderstorm": [QColor(18, 20, 28), QColor(32, 34, 46), QColor(48, 50, 68)],
    "sunset": [QColor(68, 30, 60), QColor(140, 50, 70), QColor(220, 110, 65)]
}

class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de WeatherApp Linux con fondos fotográficos atmosféricos HD,
    motor de partículas a 60 FPS superpuesto, Bento Grid Glassmorphism e interactividad total.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(560, 920)
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

        # Fondos fotográficos en memoria
        self.fondos_pixmap: Dict[str, QPixmap] = {}
        self._cargar_fondos_fotograficos()

        # Caché del fondo ya escalado al tamaño actual de la ventana,
        # para no repetir un SmoothTransformation costoso en cada repintado.
        self._fondo_escalado_cache: Optional[QPixmap] = None
        self._fondo_escalado_cache_key: Optional[tuple] = None

        # Estado
        self.ubicacion_actual = self.config_manager.obtener_ultima_ciudad()
        self.reporte_actual: Optional[ReporteClimaCompleto] = None
        self.dia_activo: Optional[PronosticoDia] = None
        self.fondo_actual_key = "clear_day"
        self.colores_cielo: List[QColor] = PALETAS_CIELO["clear_day"]

        self._init_ui()
        self._init_tray()
        self._cargar_ubicacion_inicial()

    def _cargar_fondos_fotograficos(self) -> None:
        """Carga en memoria las imágenes fotográficas atmosféricas."""
        mapeo_archivos = {
            "clear_day": "bg_clear_day.jpg",
            "clear_night": "bg_clear_night.jpg",
            "clouds_day": "bg_clouds_day.jpg",
            "clouds_night": "bg_clouds_night.jpg",
            "rain": "bg_rain.jpg",
            "snow": "bg_snow.jpg",
            "thunderstorm": "bg_thunderstorm.jpg",
            "sunset": "bg_sunset.jpg"
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

        # Motor de partículas de fondo (superpuesto a la imagen fotográfica)
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

        root_layout.addLayout(top_bar_layout)

        # 2. Área de desplazamiento
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(4, 8, 4, 16)
        self.scroll_layout.setSpacing(16)

        # Cabecera Principal
        self.cabecera = CabeceraClima(self.scroll_content)
        self.scroll_layout.addWidget(self.cabecera)

        # Tarjeta de Pronóstico 24 Horas con Curva Bézier
        self.tarjeta_horas = TarjetaBento("Pronóstico 24 Horas", "⏱️", self.scroll_content)

        self.lbl_detalle_hora = QLabel("Haz clic o desliza sobre cualquier hora para ver el pronóstico detallado", self.tarjeta_horas)
        self.lbl_detalle_hora.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.85); margin-top: -4px;")
        self.tarjeta_horas.agregar_contenido(self.lbl_detalle_hora)

        self.curva_horaria = CurvaHorariaWidget(self.tarjeta_horas)
        self.curva_horaria.hora_seleccionada.connect(self._on_hora_seleccionada)
        self.tarjeta_horas.agregar_contenido(self.curva_horaria)
        self.scroll_layout.addWidget(self.tarjeta_horas)

        # Tarjeta de Pronóstico 7 Días con Selección de Día
        self.pronostico_semanal = PronosticoSemanalWidget(self.scroll_content)
        self.pronostico_semanal.dia_seleccionado.connect(self._on_dia_seleccionado)
        self.scroll_layout.addWidget(self.pronostico_semanal)

        # Bento Grid de Tarjetas de Métricas
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

    def toggle_visibilidad(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

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

        # 1. Dibujar fotografía atmosférica escalada proporcionalmente
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
            # Centrar recorte
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

        # 2. Viñeta Glassmorphism para máximo contraste de textos blancos y tarjetas
        vignette = QLinearGradient(0, 0, 0, h)
        vignette.setColorAt(0.0, QColor(10, 15, 25, 100))
        vignette.setColorAt(0.25, QColor(10, 15, 25, 45))
        vignette.setColorAt(0.65, QColor(10, 15, 25, 60))
        vignette.setColorAt(1.0, QColor(10, 15, 25, 140))
        painter.fillRect(self.rect(), vignette)

    def _on_dia_seleccionado(self, dia: PronosticoDia) -> None:
        """Actualiza toda la interfaz (horas, métricas, cabecera y fondo) para el día seleccionado."""
        if not self.reporte_actual:
            return

        self.dia_activo = dia
        es_hoy = (dia.nombre_dia == "Hoy")

        # 1. Actualizar Curva Horaria con las 24 horas del día seleccionado
        if dia.horas:
            self.curva_horaria.set_datos(dia.horas)
        else:
            self.curva_horaria.set_datos(self.reporte_actual.horas_24h)

        # 2. Actualizar Cabecera
        if es_hoy:
            self.cabecera.actualizar_datos(self.reporte_actual)
            self.bento_grid.actualizar_datos(self.reporte_actual.actual)
            self._actualizar_paleta_cielo(self.reporte_actual.actual.condicion.animacion_tipo, self.reporte_actual.actual.condicion.es_dia)
        else:
            self.cabecera.lbl_ciudad.setText(self.ubicacion_actual.ciudad)
            region_str = f"{self.ubicacion_actual.admin1}, " if self.ubicacion_actual.admin1 and self.ubicacion_actual.admin1 != self.ubicacion_actual.ciudad else ""
            self.cabecera.lbl_pais.setText(f"{region_str}{self.ubicacion_actual.pais}")
            self.cabecera.lbl_temperatura.setText(f"{round(dia.temp_max)}°")
            self.cabecera.lbl_condicion.setText(f"{dia.condicion.descripcion} • {dia.nombre_dia}")
            self.cabecera.lbl_rango_hoy.setText(f"Máx: {round(dia.temp_max)}°  •  Mín: {round(dia.temp_min)}°")

            # Fechas del día elegido
            try:
                dt = FechaHelper.parse_iso(dia.fecha_iso)
                greg_str = FechaHelper.fecha_gregoriana_legible(dt)
                hijri_str = FechaHelper.fecha_hijri_legible(dt)
                self.cabecera.lbl_fecha_greg.setText(f"📅 {greg_str}")
                self.cabecera.lbl_fecha_hijri.setText(f"🌙 {hijri_str}")
            except Exception:
                pass

            # 3. Actualizar Bento Grid para ese día
            self.bento_grid.actualizar_por_dia(dia)

            # 4. Actualizar Fondo y Partículas
            self._actualizar_paleta_cielo(dia.condicion.animacion_tipo, es_dia=True)

        self.lbl_detalle_hora.setText(f"Mostrando pronóstico para {dia.nombre_dia} ({dia.condicion.descripcion})")
        self.update()

    def _on_hora_seleccionada(self, hora_obj: Optional[PronosticoHora]) -> None:
        """Actualiza la temperatura, Bento Grid y cielo cuando el usuario selecciona/desliza una hora."""
        if not self.reporte_actual:
            return

        if hora_obj:
            prob_str = f" • 🌧️ {hora_obj.probabilidad_lluvia}% lluvia" if hora_obj.probabilidad_lluvia > 0 else ""
            uv_str = f" • UV: {hora_obj.indice_uv:.0f}" if hora_obj.indice_uv > 0 else ""
            self.lbl_detalle_hora.setText(
                f"🕒 {hora_obj.hora_etiqueta}: {hora_obj.condicion.descripcion} • Sensación: {hora_obj.sensacion:.1f}°C{prob_str}{uv_str}"
            )

            # Actualizar temperatura y condición en la cabecera en tiempo real
            self.cabecera.lbl_temperatura.setText(f"{round(hora_obj.temperatura)}°")
            dia_ref = f" • {self.dia_activo.nombre_dia}" if self.dia_activo and self.dia_activo.nombre_dia != "Hoy" else ""
            self.cabecera.lbl_condicion.setText(f"{hora_obj.condicion.descripcion} ({hora_obj.hora_etiqueta}{dia_ref})")

            # Actualizar Bento Grid con las métricas de esa hora
            am_iso = self.reporte_actual.actual.amanecer_iso
            oc_iso = self.reporte_actual.actual.ocaso_iso
            self.bento_grid.actualizar_por_hora(hora_obj, amanecer_iso=am_iso, ocaso_iso=oc_iso)

            # Actualizar color del cielo y partículas según la hora (día/noche)
            self._actualizar_paleta_cielo(hora_obj.condicion.animacion_tipo, not hora_obj.es_noche)
        else:
            if self.dia_activo and self.dia_activo.nombre_dia != "Hoy":
                self._on_dia_seleccionado(self.dia_activo)
            else:
                self.cabecera.actualizar_datos(self.reporte_actual)
                self.bento_grid.actualizar_datos(self.reporte_actual.actual)
                self._actualizar_paleta_cielo(self.reporte_actual.actual.condicion.animacion_tipo, self.reporte_actual.actual.condicion.es_dia)
                self.lbl_detalle_hora.setText("Haz clic o desliza sobre cualquier hora para ver el pronóstico detallado")

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
        """Cambia la ubicación activa y refresca inmediatamente la pantalla."""
        self.ubicacion_actual = ubicacion
        self.dia_activo = None
        self.config_manager.guardar_ultima_ciudad(ubicacion)

        # Retroalimentación inmediata
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
            self.cabecera.lbl_condicion.setText(f"⚠️ Error al actualizar: {err}")

        ejecutar_en_segundo_plano(_fetch, on_result=_on_result, on_error=_on_error)

    def _aplicar_reporte(self, reporte: ReporteClimaCompleto) -> None:
        try:
            self.reporte_actual = reporte
            self.dia_activo = reporte.dias_7d[0] if reporte.dias_7d else None

            self.cabecera.actualizar_datos(reporte)
            self.curva_horaria.set_datos(reporte.horas_24h)
            self.pronostico_semanal.set_datos(reporte.dias_7d, temp_actual=reporte.actual.temperatura)
            self.bento_grid.actualizar_datos(reporte.actual)
            self._actualizar_paleta_cielo(reporte.actual.condicion.animacion_tipo, reporte.actual.condicion.es_dia)
            self.lbl_detalle_hora.setText("Haz clic o desliza sobre cualquier hora para ver el pronóstico detallado")

            if hasattr(self, "bandeja"):
                self.bandeja.actualizar_clima_tray(reporte)
            self.update()
        except Exception as e:
            self.cabecera.lbl_condicion.setText(f"⚠️ Error visual: {e}")

    def _actualizar_paleta_cielo(self, anim_tipo: str, es_dia: bool = True) -> None:
        # 1. Actualizar motor de partículas superpuestas
        if hasattr(self, "fondo_particulas"):
            self.fondo_particulas.set_modo_clima(anim_tipo, es_dia)

        # 2. Seleccionar clave de fondo fotográfico
        if anim_tipo == "rain":
            self.fondo_actual_key = "rain"
            self.colores_cielo = PALETAS_CIELO["rain"]
        elif anim_tipo == "snow":
            self.fondo_actual_key = "snow"
            self.colores_cielo = PALETAS_CIELO["snow"]
        elif anim_tipo == "thunderstorm":
            self.fondo_actual_key = "thunderstorm"
            self.colores_cielo = PALETAS_CIELO["thunderstorm"]
        elif anim_tipo == "clouds":
            self.fondo_actual_key = "clouds_day" if es_dia else "clouds_night"
            self.colores_cielo = PALETAS_CIELO["clouds_day"] if es_dia else PALETAS_CIELO["clouds_night"]
        elif anim_tipo == "sunset":
            self.fondo_actual_key = "sunset"
            self.colores_cielo = PALETAS_CIELO["sunset"]
        else: # clear
            self.fondo_actual_key = "clear_day" if es_dia else "clear_night"
            self.colores_cielo = PALETAS_CIELO["clear_day"] if es_dia else PALETAS_CIELO["clear_night"]

        self.update()
