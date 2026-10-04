import math
import random
from typing import List, Optional

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPaintEvent, QPen
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


# Curva de brillo de un rayo, cuadro a cuadro (~16 ms): los rayos reales
# "re-golpean" 2-3 veces por el mismo canal antes de apagarse.
_PULSOS_RAYO = [1.0, 0.55, 0.95, 0.35, 0.8, 0.6, 0.45, 0.32, 0.22, 0.14, 0.08, 0.04]


def _zigzag(inicio: QPointF, fin: QPointF, desplazamiento: float, generaciones: int) -> List[QPointF]:
    """Polilínea quebrada entre dos puntos por desplazamiento de punto medio:
    en cada generación cada tramo se parte en dos y su centro se desvía al azar."""
    puntos = [inicio, fin]
    for _ in range(generaciones):
        nuevos = [puntos[0]]
        for a, b in zip(puntos, puntos[1:]):
            medio = QPointF((a.x() + b.x()) / 2 + random.uniform(-desplazamiento, desplazamiento),
                            (a.y() + b.y()) / 2 + random.uniform(-desplazamiento, desplazamiento) * 0.3)
            nuevos += [medio, b]
        puntos = nuevos
        desplazamiento /= 1.6  # < 2: conserva quiebres bruscos en los tramos cortos
    return puntos


class Rayo:
    """Rayo con ramificaciones que parpadea y se desvanece en ~0.2 s.

    Los cercanos son largos, gruesos y con destello fuerte; los lejanos son
    cortos y tenues, y a veces solo iluminan la nube sin rayo visible."""

    def __init__(self, w: float, h: float, cercano: bool):
        self.cercano = cercano
        self.cuadro = 0
        self.visible = cercano or random.random() < 0.6  # lejanos: a veces solo destello
        self.destello_max = random.randint(130, 190) if cercano else random.randint(35, 70)
        self.grosor = random.uniform(2.0, 2.8) if cercano else random.uniform(1.0, 1.4)
        self.ramas: List[List[QPointF]] = []

        if not self.visible:
            self.tronco: List[QPointF] = []
            return

        x0 = random.uniform(w * 0.1, w * 0.9)
        inicio = QPointF(x0, random.uniform(-20, h * 0.05))
        largo = random.uniform(0.55, 0.85) if cercano else random.uniform(0.25, 0.45)
        fin = QPointF(x0 + random.uniform(-w * 0.15, w * 0.15), h * largo)
        self.tronco = _zigzag(inicio, fin, desplazamiento=w * 0.07, generaciones=5)

        # Ramas laterales que nacen del tronco y apuntan hacia abajo
        for _ in range(random.randint(2, 5) if cercano else random.randint(0, 2)):
            origen = random.choice(self.tronco[len(self.tronco) // 6: -len(self.tronco) // 4])
            dx = random.choice((-1, 1)) * random.uniform(w * 0.05, w * 0.18)
            destino = QPointF(origen.x() + dx, origen.y() + random.uniform(h * 0.06, h * 0.2))
            self.ramas.append(_zigzag(origen, destino, desplazamiento=w * 0.035, generaciones=4))

    @property
    def terminado(self) -> bool:
        return self.cuadro >= len(_PULSOS_RAYO)

    @property
    def intensidad(self) -> float:
        """Brillo actual entre 0 y 1 según la curva de pulsos."""
        return 0.0 if self.terminado else _PULSOS_RAYO[self.cuadro]

    def update(self) -> None:
        self.cuadro += 1

    def alfa_destello(self) -> int:
        return int(self.destello_max * self.intensidad)

    def dibujar(self, painter: QPainter) -> None:
        if not self.visible or self.terminado:
            return
        brillo = self.intensidad * (1.0 if self.cercano else 0.6)
        for puntos, factor in [(self.tronco, 1.0)] + [(r, 0.55) for r in self.ramas]:
            path = QPainterPath(puntos[0])
            for pt in puntos[1:]:
                path.lineTo(pt)
            g = self.grosor * factor
            # Halo azulado ancho -> capa media -> núcleo blanco
            for ancho, color, alfa in ((g * 6.0, (150, 175, 255), 0.22),
                                       (g * 2.2, (200, 215, 255), 0.45),
                                       (g, (255, 255, 255), 1.0)):
                pen = QPen(QColor(*color, int(255 * alfa * brillo * factor)), ancho)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPath(path)


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
        self.rayos: List[Rayo] = []
        self.cuadros_hasta_rayo: int = random.randint(90, 240)

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
        if self.modo_clima != "thunderstorm":
            self.rayos = []
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
        for rayo in self.rayos:
            rayo.update()
        self.rayos = [r for r in self.rayos if not r.terminado]

        self.cuadros_hasta_rayo -= 1
        if self.cuadros_hasta_rayo <= 0:
            # ~1 de cada 3 rayos es cercano; el resto, lejanos y tenues
            self.rayos.append(Rayo(float(self.width()), float(self.height()), cercano=random.random() < 0.35))
            # A veces un segundo rayo casi inmediato, como en tormentas reales
            self.cuadros_hasta_rayo = random.randint(15, 40) if random.random() < 0.25 else random.randint(150, 420)

    @property
    def relampago_alfa(self) -> int:
        """Alfa del destello de pantalla completa (el del rayo más brillante activo)."""
        return max((r.alfa_destello() for r in self.rayos), default=0)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Relámpago de fondo en tormenta: destello + rayos (detrás de la lluvia)
        if self.modo_clima == "thunderstorm":
            alfa = self.relampago_alfa
            if alfa > 0:
                painter.fillRect(self.rect(), QColor(240, 245, 255, alfa))
            for rayo in self.rayos:
                rayo.dibujar(painter)

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
