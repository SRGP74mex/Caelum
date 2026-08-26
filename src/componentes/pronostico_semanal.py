from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.componentes.curva_horaria import EMOJIS_CLIMA
from src.componentes.tarjeta_bento import TarjetaBento
from src.modelos.clima_datos import PronosticoDia


class BarraRangoTermico(QWidget):
    """
    Barra horizontal de rango térmico (mínima a máxima) con cápsula degradada
    y punto indicador de temperatura actual para el día de hoy.
    """
    def __init__(
        self,
        temp_min: float,
        temp_max: float,
        min_global: float,
        max_global: float,
        temp_actual: Optional[float] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.min_global = min_global
        self.max_global = max_global
        self.temp_actual = temp_actual
        self.setFixedHeight(12)
        self.setMinimumWidth(80)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        rango_global = max(self.max_global - self.min_global, 1.0)

        # 1. Pista de fondo translúcida
        pista_rect = QRectF(0, (h - 4) / 2.0, w, 4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        painter.drawRoundedRect(pista_rect, 2, 2)

        # 2. Cápsula de rango térmico del día
        norm_min = max(0.0, min(1.0, (self.temp_min - self.min_global) / rango_global))
        norm_max = max(0.0, min(1.0, (self.temp_max - self.min_global) / rango_global))

        x_start = norm_min * w
        x_end = norm_max * w
        ancho_capsula = max(x_end - x_start, 6.0)

        capsula_rect = QRectF(x_start, (h - 6) / 2.0, ancho_capsula, 6)

        gradiente = QLinearGradient(0, 0, w, 0)
        gradiente.setColorAt(0.0, QColor(64, 180, 240))   # Azul gélido
        gradiente.setColorAt(0.5, QColor(245, 185, 45))   # Amarillo ámbar
        gradiente.setColorAt(1.0, QColor(255, 95, 65))    # Naranja coral

        painter.setBrush(QBrush(gradiente))
        painter.drawRoundedRect(capsula_rect, 3, 3)

        # 3. Punto indicador de temperatura actual (solo si aplica hoy)
        if self.temp_actual is not None:
            norm_act = max(0.0, min(1.0, (self.temp_actual - self.min_global) / rango_global))
            dot_x = norm_act * w
            dot_y = h / 2.0

            # Borde exterior blanco
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.drawEllipse(QPointF(dot_x, dot_y), 4.5, 4.5)
            # Centro oscuro/sólido
            painter.setBrush(QColor(30, 40, 55, 255))
            painter.drawEllipse(QPointF(dot_x, dot_y), 2.5, 2.5)


class FilaDiaSemanal(QWidget):
    """
    Fila individual del pronóstico diario interactiva con clic y resaltado visual.
    """
    clicked = Signal(object) # Emite PronosticoDia

    def __init__(
        self,
        dia: PronosticoDia,
        min_global: float,
        max_global: float,
        temp_actual: Optional[float] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.dia = dia
        self.seleccionado = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(8)

        # 1. Nombre del Día ("Hoy", "Mar", etc.)
        self.lbl_nombre = QLabel(dia.nombre_dia, self)
        self.lbl_nombre.setFixedWidth(46)
        self.lbl_nombre.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff;")
        layout.addWidget(self.lbl_nombre)

        # 2. Icono Meteorológico
        emoji = EMOJIS_CLIMA.get(dia.condicion.icon_name, "⛅")
        self.lbl_icono = QLabel(emoji, self)
        self.lbl_icono.setFixedWidth(24)
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icono.setStyleSheet("font-size: 15px;")
        layout.addWidget(self.lbl_icono)

        # 3. Probabilidad de Lluvia
        prob_texto = f"🌧️ {dia.probabilidad_lluvia}%" if dia.probabilidad_lluvia >= 15 else ""
        self.lbl_lluvia = QLabel(prob_texto, self)
        self.lbl_lluvia.setFixedWidth(52)
        self.lbl_lluvia.setStyleSheet("font-size: 11px; font-weight: 700; color: rgb(100, 210, 255);")
        layout.addWidget(self.lbl_lluvia)

        # 4. Temperatura Mínima
        self.lbl_min = QLabel(f"{round(dia.temp_min)}°", self)
        self.lbl_min.setFixedWidth(28)
        self.lbl_min.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_min.setStyleSheet("font-size: 14px; color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(self.lbl_min)

        # 5. Barra de Rango Térmico
        self.barra = BarraRangoTermico(
            temp_min=dia.temp_min,
            temp_max=dia.temp_max,
            min_global=min_global,
            max_global=max_global,
            temp_actual=temp_actual,
            parent=self
        )
        layout.addWidget(self.barra, stretch=1)

        # 6. Temperatura Máxima
        self.lbl_max = QLabel(f"{round(dia.temp_max)}°", self)
        self.lbl_max.setFixedWidth(28)
        self.lbl_max.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_max.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff;")
        layout.addWidget(self.lbl_max)

    def set_seleccionado(self, valor: bool) -> None:
        self.seleccionado = valor
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit(self.dia)

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.seleccionado:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(255, 255, 255, 80), 1.0))
            painter.setBrush(QColor(255, 255, 255, 35))
            painter.drawRoundedRect(QRectF(2, 1, self.width() - 4, self.height() - 2), 10, 10)


class PronosticoSemanalWidget(TarjetaBento):
    """
    Tarjeta Bento interactiva para el pronóstico de 7 días con selección por clic.
    """
    dia_seleccionado = Signal(object) # Emite PronosticoDia

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(titulo="Pronóstico 7 Días", icono="📅", parent=parent)
        self.filas: List[FilaDiaSemanal] = []
        self.filas_layout = QVBoxLayout()
        self.filas_layout.setContentsMargins(0, 0, 0, 0)
        self.filas_layout.setSpacing(4)
        self.limpiar_contenido()
        self.contenido_layout.addLayout(self.filas_layout)

    def set_datos(self, dias: List[PronosticoDia], temp_actual: Optional[float] = None) -> None:
        # Limpiar filas previas
        while self.filas_layout.count():
            item = self.filas_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.filas = []

        if not dias:
            return

        min_global = min(d.temp_min for d in dias)
        max_global = max(d.temp_max for d in dias)

        for i, d in enumerate(dias):
            es_hoy = (i == 0)
            t_act = temp_actual if es_hoy else None
            fila = FilaDiaSemanal(
                dia=d,
                min_global=min_global,
                max_global=max_global,
                temp_actual=t_act,
                parent=self
            )
            fila.clicked.connect(self._on_fila_clicked)
            self.filas.append(fila)
            self.filas_layout.addWidget(fila)

        # Seleccionar "Hoy" por defecto
        if self.filas:
            self.filas[0].set_seleccionado(True)

    def _on_fila_clicked(self, dia: PronosticoDia) -> None:
        for fila in self.filas:
            fila.set_seleccionado(fila.dia == dia)
        self.dia_seleccionado.emit(dia)
