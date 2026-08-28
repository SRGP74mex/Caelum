import math
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from config import LUNA_DIR
from src.componentes.tarjeta_bento import TarjetaBento
from src.modelos.clima_datos import ClimaActual
from src.servicios.i18n import t
from src.utils.astronomia_utils import AstronomiaHelper
from src.utils.fecha_utils import FechaHelper
from src.utils.unidades import sufijo_temperatura, sufijo_viento

# -------------------------------------------------------------------------
# UTILIDADES VISUALES
# -------------------------------------------------------------------------

def redondear_pixmap(pixmap: QPixmap, radio: int = 14) -> QPixmap:
    """Aplica recorte con esquinas redondeadas y un borde sutil al pixmap."""
    if pixmap.isNull():
        return pixmap
    w, h = pixmap.width(), pixmap.height()
    dest = QPixmap(w, h)
    dest.fill(Qt.GlobalColor.transparent)

    painter = QPainter(dest)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    path = QPainterPath()
    path.addRoundedRect(0, 0, w, h, radio, radio)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)

    # Borde sutil traslúcido para integrarlo con Glassmorphism
    pen = QPen(QColor(255, 255, 255, 45), 1.2)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(0.6, 0.6, w - 1.2, h - 1.2, radio, radio)

    painter.end()
    return dest


# -------------------------------------------------------------------------
# WIDGETS VISUALES ESPECIALIZADOS
# -------------------------------------------------------------------------

class BrujulaWidget(QWidget):
    """Brújula gráfica interactiva que orienta una aguja según los grados del viento."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.grados: int = 0
        self.setFixedSize(70, 70)

    def set_direccion(self, grados: int) -> None:
        self.grados = grados
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2.0, self.height() / 2.0
        r = 30.0

        # Esfera exterior
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1.5))
        painter.setBrush(QColor(255, 255, 255, 15))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Puntos cardinales principales (N, E, S, O)
        font_card = QFont("-apple-system, Inter, sans-serif", 7, QFont.Weight.Bold)
        painter.setFont(font_card)
        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawText(QRectF(cx - 8, cy - r + 2, 16, 10), Qt.AlignmentFlag.AlignCenter, "N")
        painter.drawText(QRectF(cx + r - 12, cy - 5, 10, 10), Qt.AlignmentFlag.AlignCenter, "E")
        painter.drawText(QRectF(cx - 8, cy + r - 12, 16, 10), Qt.AlignmentFlag.AlignCenter, "S")
        painter.drawText(QRectF(cx - r + 2, cy - 5, 10, 10), Qt.AlignmentFlag.AlignCenter, "O")

        # Aguja de viento rotada
        rad = math.radians(self.grados - 90)  # 0 deg = Norte (arriba)
        nx = cx + math.cos(rad) * (r - 8)
        ny = cy + math.sin(rad) * (r - 8)

        # Línea de aguja hacia el origen
        painter.setPen(QPen(QColor(90, 200, 250, 255), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx, cy), QPointF(nx, ny))

        # Punto de origen central
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)


class ArcoSolarWidget(QWidget):
    """Arco solar que visualiza el recorrido del sol en tiempo real entre el amanecer y el ocaso."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.progreso_solar: float = 0.5  # 0.0 = amanecer, 0.5 = mediodía solar, 1.0 = ocaso
        self.es_de_dia: bool = True
        self.setFixedHeight(56)

    def set_tiempos(self, amanecer_iso: str, ocaso_iso: str, hora_referencia_iso: str = "") -> None:
        try:
            am_dt = FechaHelper.parse_iso(amanecer_iso)
            oc_dt = FechaHelper.parse_iso(ocaso_iso)
            if hora_referencia_iso:
                now_dt = FechaHelper.parse_iso(hora_referencia_iso)
            else:
                now_dt = datetime.now(am_dt.tzinfo) if am_dt.tzinfo else datetime.now()

            total_dia_sec = max((oc_dt - am_dt).total_seconds(), 1.0)
            elapsed_sec = (now_dt - am_dt).total_seconds()

            self.es_de_dia = (0 <= elapsed_sec <= total_dia_sec)
            self.progreso_solar = max(0.0, min(1.0, elapsed_sec / total_dia_sec))
        except Exception:
            self.progreso_solar = 0.5
            self.es_de_dia = True
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        horizon_y = h - 12.0

        p0 = QPointF(16, horizon_y)
        p1 = QPointF(w / 2.0, 6.0)
        p2 = QPointF(w - 16, horizon_y)

        # 1. Línea de horizonte
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.0, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(8, horizon_y), QPointF(w - 8, horizon_y))

        # 2. Área diurna suave bajo el arco
        path_arco = QPainterPath()
        path_arco.moveTo(p0)
        path_arco.quadTo(p1, p2)

        path_relleno = QPainterPath(path_arco)
        path_relleno.lineTo(p2.x(), horizon_y)
        path_relleno.lineTo(p0.x(), horizon_y)
        path_relleno.closeSubpath()

        grad_dia = QLinearGradient(0, 6.0, 0, horizon_y)
        if self.es_de_dia:
            grad_dia.setColorAt(0.0, QColor(255, 220, 90, 45))
            grad_dia.setColorAt(1.0, QColor(255, 180, 50, 5))
        else:
            grad_dia.setColorAt(0.0, QColor(255, 255, 255, 15))
            grad_dia.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad_dia))
        painter.drawPath(path_relleno)

        # 3. Arco completo de trayectoria
        pen_arco = QPen(QColor(255, 220, 100, 90), 2.0)
        painter.setPen(pen_arco)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_arco)

        # 4. Posición precisa del Sol sobre la curva Bézier
        t = self.progreso_solar
        sun_x = (1 - t)**2 * p0.x() + 2 * (1 - t) * t * p1.x() + t**2 * p2.x()
        sun_y = (1 - t)**2 * p0.y() + 2 * (1 - t) * t * p1.y() + t**2 * p2.y()

        # 5. Trayectoria recorrida hasta la posición actual
        if self.es_de_dia and t > 0.01:
            path_recorrido = QPainterPath()
            path_recorrido.moveTo(p0)
            steps = max(2, int(t * 30))
            for i in range(1, steps + 1):
                st = (t * i) / steps
                sx = (1 - st)**2 * p0.x() + 2 * (1 - st) * st * p1.x() + st**2 * p2.x()
                sy = (1 - st)**2 * p0.y() + 2 * (1 - st) * st * p1.y() + st**2 * p2.y()
                path_recorrido.lineTo(sx, sy)
            pen_prog = QPen(QColor(255, 235, 120, 220), 2.5)
            painter.setPen(pen_prog)
            painter.drawPath(path_recorrido)

        # 6. Renderizado del Astro Solar con Corona de Resplandor
        painter.setPen(Qt.PenStyle.NoPen)
        if self.es_de_dia:
            # Corona exterior
            painter.setBrush(QColor(255, 210, 60, 45))
            painter.drawEllipse(QPointF(sun_x, sun_y), 13.0, 13.0)
            # Resplandor medio
            painter.setBrush(QColor(255, 225, 80, 120))
            painter.drawEllipse(QPointF(sun_x, sun_y), 7.5, 7.5)
            # Núcleo brillante
            painter.setBrush(QColor(255, 255, 220, 255))
            painter.drawEllipse(QPointF(sun_x, sun_y), 4.5, 4.5)
        else:
            # Indicador de crepúsculo/noche
            painter.setBrush(QColor(180, 210, 255, 80))
            painter.drawEllipse(QPointF(sun_x, sun_y), 7.0, 7.0)
            painter.setBrush(QColor(210, 230, 255, 220))
            painter.drawEllipse(QPointF(sun_x, sun_y), 4.0, 4.0)


# -------------------------------------------------------------------------
# TARJETAS DE MÉTRICAS BENTO GRID
# -------------------------------------------------------------------------

class TarjetaIndiceUV(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.indice_uv"), icono="☀️", parent=parent)
        self.lbl_valor = QLabel("--", self)
        self.lbl_valor.setStyleSheet("font-size: 28px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_categoria = QLabel(t("uv.bajo"), self)
        self.lbl_categoria.setStyleSheet("font-size: 15px; font-weight: 500; color: rgba(255, 255, 255, 0.9);")
        self.agregar_contenido(self.lbl_categoria)

        self.lbl_desc = QLabel(t("uv.desc_bajo"), self)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.7);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.indice_uv"))
        self.lbl_valor.setText(f"{actual.indice_uv:.0f}")

        if actual.indice_uv <= 2:
            self.lbl_categoria.setText(t("uv.bajo"))
            self.lbl_desc.setText(t("uv.desc_bajo"))
        elif actual.indice_uv <= 5:
            self.lbl_categoria.setText(t("uv.moderado"))
            self.lbl_desc.setText(t("uv.desc_moderado"))
        elif actual.indice_uv <= 7:
            self.lbl_categoria.setText(t("uv.alto"))
            self.lbl_desc.setText(t("uv.desc_alto"))
        elif actual.indice_uv <= 10:
            self.lbl_categoria.setText(t("uv.muy_alto"))
            self.lbl_desc.setText(t("uv.desc_muy_alto"))
        else:
            self.lbl_categoria.setText(t("uv.extremo"))
            self.lbl_desc.setText(t("uv.desc_extremo"))


class TarjetaViento(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.viento"), icono="💨", parent=parent)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(6)

        info_v = QVBoxLayout()
        info_v.setContentsMargins(0, 0, 0, 0)
        info_v.setSpacing(2)

        self.lbl_velocidad = QLabel(f"-- {sufijo_viento()}", self)
        self.lbl_velocidad.setStyleSheet("font-size: 24px; font-weight: 600; color: #ffffff;")
        info_v.addWidget(self.lbl_velocidad)

        self.lbl_direccion = QLabel("Dirección: --", self)
        self.lbl_direccion.setStyleSheet("font-size: 13px; color: rgba(255, 255, 255, 0.9);")
        info_v.addWidget(self.lbl_direccion)

        self.lbl_rafagas = QLabel("Ráfagas: --", self)
        self.lbl_rafagas.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.7);")
        info_v.addWidget(self.lbl_rafagas)

        h_layout.addLayout(info_v, stretch=1)

        self.brujula = BrujulaWidget(self)
        h_layout.addWidget(self.brujula)

        self.contenido_layout.addLayout(h_layout)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.viento"))
        self.lbl_velocidad.setText(f"{round(actual.viento_velocidad)} {sufijo_viento()}")
        self.lbl_direccion.setText(t("viento.direccion", dir=f"{actual.viento_direccion_cardinal} ({actual.viento_direccion}°)"))
        raf_str = t("viento.rafagas", vel=f"{round(actual.viento_rafagas)} {sufijo_viento()}") if actual.viento_rafagas else t("viento.constante")
        self.lbl_rafagas.setText(raf_str)
        self.brujula.set_direccion(actual.viento_direccion)


class TarjetaSol(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.sol"), icono="🌅", parent=parent)
        self.lbl_principal = QLabel("--:--", self)
        self.lbl_principal.setStyleSheet("font-size: 26px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_principal)

        self.arco = ArcoSolarWidget(self)
        self.agregar_contenido(self.arco)

        self.lbl_secundario = QLabel("--:--", self)
        self.lbl_secundario.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_secundario)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.sol"))
        if actual.amanecer_iso and actual.ocaso_iso:
            am_str = FechaHelper.formato_hora_corta(actual.amanecer_iso)
            oc_str = FechaHelper.formato_hora_corta(actual.ocaso_iso)

            self.arco.set_tiempos(actual.amanecer_iso, actual.ocaso_iso)
            if self.arco.es_de_dia:
                self.lbl_principal.setText(t("sol.ocaso_hoy", hora=oc_str))
                self.lbl_secundario.setText(t("sol.amanecer_fue", hora=am_str))
            else:
                self.lbl_principal.setText(t("sol.amanecer_hoy", hora=am_str))
                self.lbl_secundario.setText(t("sol.ocaso_fue", hora=oc_str))


class TarjetaHumedad(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.humedad"), icono="💧", parent=parent)
        self.lbl_valor = QLabel("--%", self)
        self.lbl_valor.setStyleSheet("font-size: 28px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_punto_rocio = QLabel(f"--{sufijo_temperatura()}", self)
        self.lbl_punto_rocio.setWordWrap(True)
        self.lbl_punto_rocio.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_punto_rocio)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.humedad"))
        self.lbl_valor.setText(f"{actual.humedad_relativa}%")
        rocio_str = f"{actual.punto_rocio:.1f}{sufijo_temperatura()}" if actual.punto_rocio is not None else "--"
        self.lbl_punto_rocio.setText(t("humedad.rocio_desc", rocio=rocio_str))


class TarjetaPresion(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.presion"), icono="📊", parent=parent)
        self.lbl_valor = QLabel("-- hPa", self)
        self.lbl_valor.setStyleSheet("font-size: 26px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_desc = QLabel(t("presion.normal"), self)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.presion"))
        self.lbl_valor.setText(f"{actual.presion_hpa:.0f} hPa")
        if actual.presion_hpa < 1000:
            self.lbl_desc.setText(t("presion.baja"))
        elif actual.presion_hpa > 1020:
            self.lbl_desc.setText(t("presion.alta"))
        else:
            self.lbl_desc.setText(t("presion.normal"))


class TarjetaVisibilidad(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.visibilidad"), icono="👁️", parent=parent)
        self.lbl_valor = QLabel("-- km", self)
        self.lbl_valor.setStyleSheet("font-size: 26px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_desc = QLabel(t("visibilidad.excelente"), self)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.visibilidad"))
        self.lbl_valor.setText(f"{actual.visibilidad_km:.1f} km")
        if actual.visibilidad_km >= 10:
            self.lbl_desc.setText(t("visibilidad.excelente"))
        elif actual.visibilidad_km >= 5:
            self.lbl_desc.setText(t("visibilidad.moderada"))
        else:
            self.lbl_desc.setText(t("visibilidad.reducida"))


class TarjetaFaseLunar(TarjetaBento):
    """
    Tarjeta Bento astronómica que presenta la fase lunar actual con imagen PNG de alta
    resolución ocupando el 100% del alto de la tarjeta, esquinas redondeadas y centrada verticalmente.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.luna"), icono="🌙", parent=parent)
        self.pixmap_original: Optional[QPixmap] = None

        # Reducir márgenes para que la luna llene el alto completo
        self.main_layout.setContentsMargins(16, 12, 12, 12)
        self.main_layout.setSpacing(8)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(14)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        info_v = QVBoxLayout()
        info_v.setContentsMargins(0, 0, 0, 0)
        info_v.setSpacing(4)
        info_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_fase = QLabel(t("luna.llena"), self)
        self.lbl_fase.setStyleSheet("font-size: 20px; font-weight: 700; color: #ffffff;")
        info_v.addWidget(self.lbl_fase)

        self.lbl_iluminacion = QLabel("Iluminación: --%", self)
        self.lbl_iluminacion.setStyleSheet("font-size: 13px; font-weight: 500; color: rgba(255, 255, 255, 0.95);")
        info_v.addWidget(self.lbl_iluminacion)

        self.lbl_horarios = QLabel("Salida: --:-- • Puesta: --:--", self)
        self.lbl_horarios.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.78);")
        info_v.addWidget(self.lbl_horarios)

        self.lbl_proxima = QLabel("Próx. luna llena: --", self)
        self.lbl_proxima.setStyleSheet("font-size: 11px; font-weight: 600; color: #60a5fa;")
        info_v.addWidget(self.lbl_proxima)

        h_layout.addLayout(info_v, stretch=1)

        # Contenedor de la Luna ocupando el 100% del alto del contenido con esquinas redondeadas
        self.lbl_icono = QLabel(self)
        self.lbl_icono.setFixedSize(110, 110)
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(self.lbl_icono, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.contenido_layout.addLayout(h_layout)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._actualizar_pixmap()

    def _actualizar_pixmap(self) -> None:
        if not self.pixmap_original or self.pixmap_original.isNull():
            return

        # Calcular el 100% del alto del área de contenido disponible
        alto_disponible = self.contenido_widget.height()
        if alto_disponible <= 0:
            alto_disponible = max(self.height() - 44, 105)

        tam = max(96, min(alto_disponible, 130))

        self.lbl_icono.setFixedSize(tam, tam)
        scaled = self.pixmap_original.scaled(
            tam, tam,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        rounded = redondear_pixmap(scaled, radio=14)
        self.lbl_icono.setPixmap(rounded)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.luna"))
        info_luna = AstronomiaHelper.obtener_info_lunar(
            fecha=None,
            amanecer_iso=actual.amanecer_iso,
            ocaso_iso=actual.ocaso_iso
        )
        self.lbl_fase.setText(info_luna.nombre)
        self.lbl_iluminacion.setText(t("luna.iluminacion", pct=info_luna.iluminacion_pct, dias=info_luna.edad_dias))
        self.lbl_horarios.setText(t("luna.salida_puesta", salida=info_luna.salida_estimada, puesta=info_luna.puesta_estimada))
        self.lbl_proxima.setText(t("luna.prox_llena", fecha=info_luna.proxima_luna_llena))

        icono_path = LUNA_DIR / info_luna.archivo_icono
        if icono_path.exists():
            pix = QPixmap(str(icono_path))
            if not pix.isNull():
                self.pixmap_original = pix
                self._actualizar_pixmap()


class TarjetaCalidadAire(TarjetaBento):
    """
    Tarjeta Bento ambiental que reporta el índice AQI, nivel de riesgo con semáforo
    visual y concentración de micropartículas PM2.5 / PM10.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo=t("bento.calidad_aire"), icono="🍃", parent=parent)
        h_top = QHBoxLayout()
        h_top.setContentsMargins(0, 0, 0, 0)
        h_top.setSpacing(8)

        self.lbl_aqi = QLabel("--", self)
        self.lbl_aqi.setStyleSheet("font-size: 28px; font-weight: 600; color: #ffffff;")
        h_top.addWidget(self.lbl_aqi)

        self.badge_nivel = QLabel(t("calidad_aire.buena"), self)
        self.badge_nivel.setStyleSheet("""
            background-color: rgba(52, 211, 153, 0.25);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.4);
            border-radius: 8px;
            padding: 3px 8px;
            font-size: 12px;
            font-weight: 600;
        """)
        h_top.addWidget(self.badge_nivel)
        h_top.addStretch()

        self.contenido_layout.addLayout(h_top)

        self.lbl_particulas = QLabel("PM2.5: -- μg/m³ • PM10: -- μg/m³", self)
        self.lbl_particulas.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.85);")
        self.agregar_contenido(self.lbl_particulas)

        self.lbl_desc = QLabel(t("calidad_aire.desc_buena"), self)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.7);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_titulo.setText(t("bento.calidad_aire"))
        if actual.calidad_aire:
            ca = actual.calidad_aire
            self.lbl_aqi.setText(f"{ca.aqi_us}")

            if ca.aqi_us <= 50:
                cat_txt = t("calidad_aire.buena")
                desc_txt = t("calidad_aire.desc_buena")
            elif ca.aqi_us <= 100:
                cat_txt = t("calidad_aire.moderada")
                desc_txt = t("calidad_aire.desc_moderada")
            elif ca.aqi_us <= 150:
                cat_txt = t("calidad_aire.sensible")
                desc_txt = t("calidad_aire.desc_sensible")
            elif ca.aqi_us <= 200:
                cat_txt = t("calidad_aire.insalubre")
                desc_txt = t("calidad_aire.desc_insalubre")
            elif ca.aqi_us <= 300:
                cat_txt = t("calidad_aire.muy_insalubre")
                desc_txt = t("calidad_aire.desc_muy_insalubre")
            else:
                cat_txt = t("calidad_aire.peligrosa")
                desc_txt = t("calidad_aire.desc_peligrosa")

            self.badge_nivel.setText(cat_txt)
            color = ca.color_hex
            self.badge_nivel.setStyleSheet(f"""
                background-color: {color}33;
                color: {color};
                border: 1px solid {color}88;
                border-radius: 8px;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: 600;
            """)
            self.lbl_particulas.setText(t("calidad_aire.particulas", pm25=f"{ca.pm2_5:.1f}", pm10=f"{ca.pm10:.1f}"))
            self.lbl_desc.setText(desc_txt)
        else:
            self.lbl_aqi.setText("35")
            self.badge_nivel.setText(t("calidad_aire.buena"))
            self.lbl_particulas.setText(t("calidad_aire.particulas", pm25="8.5", pm10="14.0"))
            self.lbl_desc.setText(t("calidad_aire.desc_buena"))
