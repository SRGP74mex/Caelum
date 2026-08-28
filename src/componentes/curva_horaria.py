from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPaintEvent, QPen
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
    hora_seleccionada = Signal(object) # Emite PronosticoHora al hacer clic

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
        self.selected_index = 0 if horas else None
        self.hover_index = None
        self.setFixedWidth(len(horas) * self.col_width)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x = event.position().x()
        idx = int(x // self.col_width)
        if 0 <= idx < len(self.horas):
            if self.hover_index != idx:
                self.hover_index = idx
                self.update()

    def leaveEvent(self, event) -> None:
        self.hover_index = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        x = event.position().x()
        idx = int(x // self.col_width)
        if 0 <= idx < len(self.horas):
            self.selected_index = idx
            self.hora_seleccionada.emit(self.horas[idx])
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self.horas:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        h = self.height()

        temps = [h_obj.temperatura for h_obj in self.horas]
        min_temp, max_temp = min(temps), max(temps)
        temp_range = max(max_temp - min_temp, 2.0)

        curve_area_height = h - self.curve_top_offset - self.margin_bottom

        # 1. Calcular puntos de la curva
        puntos: List[QPointF] = []
        for i, h_obj in enumerate(self.horas):
            cx = (i * self.col_width) + (self.col_width / 2.0)
            norm = (h_obj.temperatura - min_temp) / temp_range
            cy = (h - self.margin_bottom) - (norm * curve_area_height)
            puntos.append(QPointF(cx, cy))

        # 2. Dibujar relleno con degradado bajo la curva Bézier
        if len(puntos) >= 2:
            path = QPainterPath(puntos[0])
            for i in range(len(puntos) - 1):
                p1 = puntos[i]
                p2 = puntos[i + 1]
                mid_x = (p1.x() + p2.x()) / 2.0
                path.cubicTo(QPointF(mid_x, p1.y()), QPointF(mid_x, p2.y()), p2)

            fill_path = QPainterPath(path)
            fill_path.lineTo(puntos[-1].x(), h)
            fill_path.lineTo(puntos[0].x(), h)
            fill_path.closeSubpath()

            gradiente = QLinearGradient(0, self.curve_top_offset, 0, h)
            temp_prom = sum(temps) / len(temps)
            if temp_prom >= 18:
                gradiente.setColorAt(0.0, QColor(255, 170, 40, 115))
                gradiente.setColorAt(0.7, QColor(255, 120, 20, 45))
                gradiente.setColorAt(1.0, QColor(255, 120, 20, 0))
            else:
                gradiente.setColorAt(0.0, QColor(90, 200, 250, 115))
                gradiente.setColorAt(0.7, QColor(50, 150, 230, 45))
                gradiente.setColorAt(1.0, QColor(50, 150, 230, 0))

            painter.fillPath(fill_path, QBrush(gradiente))

            # 3. Línea continua de la curva
            pen_linea = QPen(QColor(255, 255, 255, 220), 2.5)
            painter.setPen(pen_linea)
            painter.drawPath(path)

        # 4. Dibujar columnas
        font_hora = QFont("-apple-system, Inter, sans-serif", 10, QFont.Weight.Medium)
        font_temp = QFont("-apple-system, Inter, sans-serif", 10, QFont.Weight.Bold)
        font_rain = QFont("-apple-system, Inter, sans-serif", 8, QFont.Weight.Bold)
        font_emoji = QFont("sans-serif", 13)

        for i, h_obj in enumerate(self.horas):
            col_x = i * self.col_width
            cx = puntos[i].x()
            cy = puntos[i].y()
            es_seleccionado = (self.selected_index == i)
            es_hovered = (self.hover_index == i)

            # Resaltado de fondo de columna seleccionada o hover
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
