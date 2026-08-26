import math
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QLinearGradient,
    QColor, QPainterPath, QFont, QPaintEvent
)
from typing import Optional

from src.modelos.clima_datos import ClimaActual
from src.componentes.tarjeta_bento import TarjetaBento
from src.utils.fecha_utils import FechaHelper

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
        rad = math.radians(self.grados - 90) # 0 deg = Norte (arriba)
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
    """Arco solar que visualiza el recorrido del sol entre el amanecer y el ocaso."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.progreso_solar: float = 0.5 # 0.0 = amanecer, 0.5 = mediodía, 1.0 = ocaso
        self.es_de_dia: bool = True
        self.setFixedHeight(50)

    def set_tiempos(self, amanecer_iso: str, ocaso_iso: str) -> None:
        try:
            am_dt = FechaHelper.parse_iso(amanecer_iso)
            oc_dt = FechaHelper.parse_iso(ocaso_iso)
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
        horizon_y = h - 10.0

        # Línea de horizonte
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1.0, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(10, horizon_y), QPointF(w - 10, horizon_y))

        # Arco solar
        path = QPainterPath()
        path.moveTo(15, horizon_y)
        path.quadTo(w / 2.0, 4.0, w - 15, horizon_y)

        painter.setPen(QPen(QColor(255, 215, 60, 100), 2.0))
        painter.drawPath(path)

        # Posición del sol sobre el arco cuadrático
        t = self.progreso_solar
        p0 = QPointF(15, horizon_y)
        p1 = QPointF(w / 2.0, 4.0)
        p2 = QPointF(w - 15, horizon_y)

        sun_x = (1 - t)**2 * p0.x() + 2 * (1 - t) * t * p1.x() + t**2 * p2.x()
        sun_y = (1 - t)**2 * p0.y() + 2 * (1 - t) * t * p1.y() + t**2 * p2.y()

        # Resplandor solar
        painter.setPen(Qt.PenStyle.NoPen)
        if self.es_de_dia:
            painter.setBrush(QColor(255, 215, 60, 100))
            painter.drawEllipse(QPointF(sun_x, sun_y), 7.0, 7.0)
            painter.setBrush(QColor(255, 240, 150, 255))
            painter.drawEllipse(QPointF(sun_x, sun_y), 4.0, 4.0)
        else:
            painter.setBrush(QColor(180, 210, 255, 180))
            painter.drawEllipse(QPointF(sun_x, sun_y), 4.0, 4.0)


# -------------------------------------------------------------------------
# TARJETAS DE MÉTRICAS BENTO GRID
# -------------------------------------------------------------------------

class TarjetaIndiceUV(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Índice UV", icono="☀️", parent=parent)
        self.lbl_valor = QLabel("--", self)
        self.lbl_valor.setStyleSheet("font-size: 28px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_categoria = QLabel("Bajo", self)
        self.lbl_categoria.setStyleSheet("font-size: 15px; font-weight: 500; color: rgba(255, 255, 255, 0.9);")
        self.agregar_contenido(self.lbl_categoria)

        self.lbl_desc = QLabel("No se requiere protección especial.", self)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.7);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_valor.setText(f"{actual.indice_uv:.0f}")
        self.lbl_categoria.setText(actual.uv_categoria)

        if actual.indice_uv <= 2:
            self.lbl_desc.setText("Nivel seguro. Disfruta del aire libre.")
        elif actual.indice_uv <= 5:
            self.lbl_desc.setText("Usa gafas de sol y protector solar.")
        elif actual.indice_uv <= 7:
            self.lbl_desc.setText("Protección solar necesaria entre 10:00 y 16:00.")
        else:
            self.lbl_desc.setText("Extrema precaución. Busca la sombra.")


class TarjetaViento(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Viento", icono="💨", parent=parent)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(6)

        info_v = QVBoxLayout()
        info_v.setContentsMargins(0, 0, 0, 0)
        info_v.setSpacing(2)

        self.lbl_velocidad = QLabel("-- km/h", self)
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
        self.lbl_velocidad.setText(f"{round(actual.viento_velocidad)} km/h")
        self.lbl_direccion.setText(f"{actual.viento_direccion_cardinal} ({actual.viento_direccion}°)")
        raf_str = f"Ráfagas: {round(actual.viento_rafagas)} km/h" if actual.viento_rafagas else "Viento constante"
        self.lbl_rafagas.setText(raf_str)
        self.brujula.set_direccion(actual.viento_direccion)


class TarjetaSol(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Amanecer / Ocaso", icono="🌅", parent=parent)
        self.lbl_principal = QLabel("--:--", self)
        self.lbl_principal.setStyleSheet("font-size: 26px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_principal)

        self.arco = ArcoSolarWidget(self)
        self.agregar_contenido(self.arco)

        self.lbl_secundario = QLabel("Puesta de sol: --:--", self)
        self.lbl_secundario.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_secundario)

    def actualizar(self, actual: ClimaActual) -> None:
        if actual.amanecer_iso and actual.ocaso_iso:
            am_str = FechaHelper.formato_hora_corta(actual.amanecer_iso)
            oc_str = FechaHelper.formato_hora_corta(actual.ocaso_iso)

            self.arco.set_tiempos(actual.amanecer_iso, actual.ocaso_iso)
            if self.arco.es_de_dia:
                self.lbl_principal.setText(f"Ocaso: {oc_str}")
                self.lbl_secundario.setText(f"Amanecer hoy fue a las {am_str}")
            else:
                self.lbl_principal.setText(f"Amanecer: {am_str}")
                self.lbl_secundario.setText(f"Ocaso fue a las {oc_str}")


class TarjetaHumedad(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Humedad", icono="💧", parent=parent)
        self.lbl_valor = QLabel("--%", self)
        self.lbl_valor.setStyleSheet("font-size: 28px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_punto_rocio = QLabel("Punto de rocío: --°C", self)
        self.lbl_punto_rocio.setWordWrap(True)
        self.lbl_punto_rocio.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_punto_rocio)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_valor.setText(f"{actual.humedad_relativa}%")
        rocio_str = f"{actual.punto_rocio:.1f}°C" if actual.punto_rocio is not None else "--"
        self.lbl_punto_rocio.setText(f"El punto de rocío es de {rocio_str} en este momento.")


class TarjetaPresion(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Presión", icono="📊", parent=parent)
        self.lbl_valor = QLabel("-- hPa", self)
        self.lbl_valor.setStyleSheet("font-size: 26px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_desc = QLabel("Presión atmosférica normal", self)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_valor.setText(f"{actual.presion_hpa:.0f} hPa")
        if actual.presion_hpa < 1000:
            self.lbl_desc.setText("Presión baja • Posible nubosidad")
        elif actual.presion_hpa > 1020:
            self.lbl_desc.setText("Presión alta • Tiempo estable")
        else:
            self.lbl_desc.setText("Presión atmosférica típica")


class TarjetaVisibilidad(TarjetaBento):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Visibilidad", icono="👁️", parent=parent)
        self.lbl_valor = QLabel("-- km", self)
        self.lbl_valor.setStyleSheet("font-size: 26px; font-weight: 600; color: #ffffff;")
        self.agregar_contenido(self.lbl_valor)

        self.lbl_desc = QLabel("Buena visibilidad", self)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.75);")
        self.agregar_contenido(self.lbl_desc)

    def actualizar(self, actual: ClimaActual) -> None:
        self.lbl_valor.setText(f"{actual.visibilidad_km:.1f} km")
        if actual.visibilidad_km >= 10:
            self.lbl_desc.setText("Visibilidad perfectamente clara.")
        elif actual.visibilidad_km >= 5:
            self.lbl_desc.setText("Ligera neblina en el horizonte.")
        else:
            self.lbl_desc.setText("Visibilidad reducida por niebla/precipitaciones.")

