from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QScrollArea, QWidget

from src.modelos.clima_datos import PronosticoHora

# Mapeo de animación/icono a emoji ilustrativo
EMOJIS_CLIMA = {
    "clear-day": "☀️",
    "clear-night": "🌙",
    "partly-cloudy-day": "⛅",
    "partly-cloudy-night": "☁️",
    "cloudy": "☁️",
    "drizzle": "🌧️",
    "drizzle-day": "🌦️",
    "drizzle-night": "🌧️",
    "partly-cloudy-day-rain": "🌦️",
    "partly-cloudy-night-rain": "🌧️",
    "rain": "🌧️",
    "heavy-rain": "🌧️",
    "thunderstorms-day": "⛈️",
    "thunderstorms-night": "⛈️",
    "thunderstorms-day-rain": "⛈️",
    "thunderstorms-night-rain": "⛈️",
    "snow": "❄️",
    "heavy-snow": "🌨️",
    "partly-cloudy-day-snow": "🌨️",
    "partly-cloudy-night-snow": "🌨️",
    "fog-day": "🌫️",
    "fog-night": "🌫️",
    "snowflake": "❄️",
    "sleet": "🌨️",
    "sleet-day": "🌨️",
    "sleet-night": "🌨️",
}


class LienzoCurvaHoraria(QWidget):
    """
    Lienzo de dibujo personalizado que renderiza una curva suave Bézier de temperatura,
    iconos, etiquetas de hora y probabilidad de lluvia con selección por clic.
    """
    hora_seleccionada = Signal(object)  # Emite PronosticoHora al hacer clic

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.horas: List[PronosticoHora] = []
        self.selected_index: Optional[int] = 0
        self.hover_index: Optional[int] = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(155)

        # Dimensiones de cada columna de hora
        self.col_width = 54
        self.margin_top = 8
        self.margin_bottom = 22
        self.curve_top_offset = 64

    def set_datos(self, horas: List[PronosticoHora]) -> None:
        self.horas = horas
        if self.horas:
            self.setFixedWidth(len(self.horas) * self.col_width)
            self.selected_index = 0
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.horas:
            return
        idx = int(event.position().x() // self.col_width)
        if 0 <= idx < len(self.horas):
            self.selected_index = idx
            self.hora_seleccionada.emit(self.horas[idx])
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.horas:
            return
        idx = int(event.position().x() // self.col_width)
        if 0 <= idx < len(self.horas) and idx != self.hover_index:
            self.hover_index = idx
            self.update()

    def leaveEvent(self, event) -> None:
        self.hover_index = None
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self.horas:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        n = len(self.horas)

        temps = [h_obj.temperatura for h_obj in self.horas]
        min_temp = min(temps)
        max_temp = max(temps)
        temp_range = max_temp - min_temp if max_temp != min_temp else 1.0

        # Rango vertical disponible para la curva
        curve_y_min = self.curve_top_offset + 10
        curve_y_max = h - self.margin_bottom - 10

        # Calcular coordenadas (x, y) de cada punto
        puntos = []
        for i, h_obj in enumerate(self.horas):
            cx = i * self.col_width + self.col_width / 2.0
            # Mapeo invertido: mayor temperatura -> menor Y (arriba)
            ratio = (h_obj.temperatura - min_temp) / temp_range
            cy = curve_y_max - ratio * (curve_y_max - curve_y_min)
            puntos.append(QPointF(cx, cy))

        # 1. Dibujar Gradiente de Área bajo la Curva
        if len(puntos) > 1:
            path_area = QPainterPath()
            path_area.moveTo(puntos[0].x(), h)
            path_area.lineTo(puntos[0])

            for i in range(len(puntos) - 1):
                p0 = puntos[i]
                p1 = puntos[i + 1]
                dx = (p1.x() - p0.x()) / 2.0
                c1 = QPointF(p0.x() + dx, p0.y())
                c2 = QPointF(p1.x() - dx, p1.y())
                path_area.cubicTo(c1, c2, p1)

            path_area.lineTo(puntos[-1].x(), h)
            path_area.closeSubpath()

            grad_area = QLinearGradient(0, curve_y_min, 0, h)
            grad_area.setColorAt(0.0, QColor(255, 255, 255, 60))
            grad_area.setColorAt(0.6, QColor(255, 255, 255, 15))
            grad_area.setColorAt(1.0, QColor(255, 255, 255, 0))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad_area))
            painter.drawPath(path_area)

            # 2. Dibujar Línea de la Curva
            path_linea = QPainterPath()
            path_linea.moveTo(puntos[0])
            for i in range(len(puntos) - 1):
                p0 = puntos[i]
                p1 = puntos[i + 1]
                dx = (p1.x() - p0.x()) / 2.0
                c1 = QPointF(p0.x() + dx, p0.y())
                c2 = QPointF(p1.x() - dx, p1.y())
                path_linea.cubicTo(c1, c2, p1)

            pen_linea = QPen(QColor(255, 255, 255, 220), 2.5)
            painter.setPen(pen_linea)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path_linea)

        # 3. Dibujar Columnas de Texto, Emojis y Puntos
        font_hora = QFont("-apple-system", 10, QFont.Weight.Medium)
        font_emoji = QFont("Apple Color Emoji", 14)
        font_temp = QFont("-apple-system", 11, QFont.Weight.DemiBold)
        font_rain = QFont("-apple-system", 9, QFont.Weight.Medium)

        for i, (h_obj, p) in enumerate(zip(self.horas, puntos)):
            col_x = i * self.col_width
            cx = p.x()
            cy = p.y()
            es_seleccionado = (i == self.selected_index)
            es_hovered = (i == self.hover_index and not es_seleccionado)

            # Resaltado de Columna
            if es_seleccionado:
                painter.fillRect(
                    QRectF(col_x, 0, self.col_width, h),
                    QColor(255, 255, 255, 45)
                )
            elif es_hovered:
                painter.fillRect(
                    QRectF(col_x, 0, self.col_width, h),
                    QColor(255, 255, 255, 20)
                )

            # Hora
            painter.setFont(font_hora)
            painter.setPen(QColor(255, 255, 255, 255 if es_seleccionado else 210))
            painter.drawText(
                QRectF(col_x, self.margin_top, self.col_width, 16),
                Qt.AlignmentFlag.AlignCenter,
                h_obj.hora_etiqueta
            )

            # Icono Emoji
            default_fallback = "🌙" if h_obj.es_noche else "☀️"
            emoji = EMOJIS_CLIMA.get(h_obj.condicion.icon_name, default_fallback)
            painter.setFont(font_emoji)
            painter.drawText(
                QRectF(col_x, self.margin_top + 18, self.col_width, 20),
                Qt.AlignmentFlag.AlignCenter,
                emoji
            )

            # Probabilidad de lluvia
            if h_obj.probabilidad_lluvia >= 15:
                painter.setFont(font_rain)
                painter.setPen(QColor(100, 210, 255, 240))
                painter.drawText(
                    QRectF(col_x, self.margin_top + 38, self.col_width, 14),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{h_obj.probabilidad_lluvia}%"
                )

            # Punto en la curva
            if es_seleccionado:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 120))
                painter.drawEllipse(QPointF(cx, cy), 8, 8)
                painter.setBrush(QColor(255, 255, 255, 255))
                painter.drawEllipse(QPointF(cx, cy), 4.5, 4.5)
            elif es_hovered:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 80))
                painter.drawEllipse(QPointF(cx, cy), 6, 6)
                painter.setBrush(QColor(255, 255, 255, 230))
                painter.drawEllipse(QPointF(cx, cy), 3.5, 3.5)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.drawEllipse(QPointF(cx, cy), 3, 3)

            # Temperatura arriba del punto
            painter.setFont(font_temp)
            painter.setPen(QColor(255, 255, 255, 255 if es_seleccionado else 230))
            painter.drawText(
                QRectF(col_x, cy - 18, self.col_width, 16),
                Qt.AlignmentFlag.AlignCenter,
                f"{round(h_obj.temperatura)}°"
            )


class CurvaHorariaWidget(QScrollArea):
    """
    Contenedor deslizable horizontalmente para la curva horaria interactiva de 24 horas.
    """
    hora_seleccionada = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFixedHeight(165)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 4px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.25);
                min-width: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.50);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                border: none;
            }
        """)

        self.lienzo = LienzoCurvaHoraria(self)
        self.lienzo.hora_seleccionada.connect(self.hora_seleccionada)
        self.setWidget(self.lienzo)

    def set_datos(self, horas: List[PronosticoHora]) -> None:
        self.lienzo.set_datos(horas)
