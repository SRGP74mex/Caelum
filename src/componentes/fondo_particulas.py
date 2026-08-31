import math
import random
from typing import List, Optional

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget


class GotaLluvia:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.reset(random_y=True)

    def reset(self, random_y: bool = False) -> None:
        self.x = random.uniform(0, self.w + 100)
        self.y = random.uniform(0, self.h) if random_y else random.uniform(-40, -10)
        self.speed = random.uniform(14, 22)
        self.length = random.uniform(14, 26)
        self.alpha = random.randint(90, 180)
        self.slant = -3.0 # Inclinación sutil por viento

    def update(self) -> None:
        self.y += self.speed
        self.x += self.slant
        if self.y > self.h or self.x < -20:
            self.reset(random_y=False)


class CopoNieve:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.reset(random_y=True)

    def reset(self, random_y: bool = False) -> None:
        self.base_x = random.uniform(0, self.w)
        self.x = self.base_x
        self.y = random.uniform(0, self.h) if random_y else random.uniform(-20, -5)
        self.speed = random.uniform(1.2, 2.8)
        self.radius = random.uniform(1.5, 3.5)
        self.alpha = random.randint(120, 220)
        self.angle = random.uniform(0, math.pi * 2)
        self.sway_speed = random.uniform(0.02, 0.05)
        self.sway_amp = random.uniform(15, 35)

    def update(self) -> None:
        self.y += self.speed
        self.angle += self.sway_speed
        self.x = self.base_x + math.sin(self.angle) * self.sway_amp
        if self.y > self.h:
            self.reset(random_y=False)


class Estrella:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.x = random.uniform(0, self.w)
        self.y = random.uniform(0, self.h * 0.7) # Parte superior del cielo
        self.radius = random.uniform(0.8, 2.0)
        self.base_alpha = random.randint(80, 180)
        self.phase = random.uniform(0, math.pi * 2)
        self.twinkle_speed = random.uniform(0.03, 0.08)

    def get_alpha(self) -> int:
        self.phase += self.twinkle_speed
        factor = (math.sin(self.phase) + 1.0) / 2.0
        return int(self.base_alpha * (0.4 + 0.6 * factor))


class FondoParticulasWidget(QWidget):
    """
    Widget de animación de partículas nativas a 60 FPS (lluvia, nieve, estrellas, relámpagos).
    Optimizado en QPainter, con <1% de consumo de CPU.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self.modo_clima: str = "clear" # "rain", "snow", "thunderstorm", "clear_night", "clear_day"
        self.es_dia: bool = True

        self.gotas: List[GotaLluvia] = []
        self.copos: List[CopoNieve] = []
        self.estrellas: List[Estrella] = []

        # Estado para relámpagos
        self.relampago_alfa: int = 0
        self.cuenta_relampago: int = 0

        self._init_particulas(540, 840)

        # Timer de animación a 60 FPS (~16 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    def pausar(self) -> None:
        """Detiene el timer de animación. Úsese cuando la ventana no es visible
        (minimizada u oculta en la bandeja) para no gastar CPU en segundo plano."""
        self.timer.stop()

    def reanudar(self) -> None:
        """Reinicia el timer de animación tras una llamada a pausar()."""
        if not self.timer.isActive():
            self.timer.start(16)

    def _init_particulas(self, w: float, h: float) -> None:
        if w <= 0 or h <= 0:
            return
        self.gotas = [GotaLluvia(w, h) for _ in range(90)]
        self.copos = [CopoNieve(w, h) for _ in range(60)]
        self.estrellas = [Estrella(w, h) for _ in range(50)]

    def resizeEvent(self, event) -> None:
        self._init_particulas(float(self.width()), float(self.height()))

    def set_modo_clima(self, tipo_animacion: str, es_dia: bool = True) -> None:
        """Cambia el modo del sistema de partículas según el clima actual."""
        self.es_dia = es_dia
        if tipo_animacion in ["rain", "snow", "thunderstorm"]:
            self.modo_clima = tipo_animacion
        elif not es_dia:
            self.modo_clima = "clear_night"
        else:
            self.modo_clima = "clear_day"
        self.update()

    def _on_tick(self) -> None:
        if self.modo_clima in ["rain", "thunderstorm"]:
            for g in self.gotas:
                g.update()

            if self.modo_clima == "thunderstorm":
                self._update_relampago()

            self.update()

        elif self.modo_clima == "snow":
            for c in self.copos:
                c.update()
            self.update()

        elif self.modo_clima == "clear_night":
            self.update() # Para titileo de estrellas

    def _update_relampago(self) -> None:
        if self.relampago_alfa > 0:
            self.relampago_alfa = max(0, self.relampago_alfa - 25)
        else:
            self.cuenta_relampago += 1
            if self.cuenta_relampago > 240 and random.random() < 0.03:
                self.relampago_alfa = random.randint(140, 210)
                self.cuenta_relampago = 0

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Relámpago de fondo en tormenta
        if self.modo_clima == "thunderstorm" and self.relampago_alfa > 0:
            painter.fillRect(self.rect(), QColor(240, 245, 255, self.relampago_alfa))

        # 2. Lluvia
        if self.modo_clima in ["rain", "thunderstorm"]:
            for g in self.gotas:
                pen = QPen(QColor(190, 225, 255, g.alpha), 1.5)
                painter.setPen(pen)
                painter.drawLine(
                    QPointF(g.x, g.y),
                    QPointF(g.x + g.slant, g.y + g.length)
                )

        # 3. Nieve
        elif self.modo_clima == "snow":
            painter.setPen(Qt.PenStyle.NoPen)
            for c in self.copos:
                painter.setBrush(QColor(255, 255, 255, c.alpha))
                painter.drawEllipse(QPointF(c.x, c.y), c.radius, c.radius)

        # 4. Noche Estrellada
        elif self.modo_clima == "clear_night":
            painter.setPen(Qt.PenStyle.NoPen)
            for e in self.estrellas:
                alfa = e.get_alpha()
                painter.setBrush(QColor(255, 255, 255, alfa))
                painter.drawEllipse(QPointF(e.x, e.y), e.radius, e.radius)
