from typing import Optional

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.servicios.i18n import t

# Colores de los "semáforos" estilo macOS (cerrar, minimizar, maximizar)
COLOR_CERRAR = "#ff5f57"
COLOR_MINIMIZAR = "#febc2e"
COLOR_MAXIMIZAR = "#28c840"

# Grosor de la zona sensible para redimensionar desde los bordes de la ventana sin marco
GROSOR_BORDE = 6


class BarraTitulo(QWidget):
    """Barra de título compacta para la ventana sin marco, con botones circulares de
    colores y movimiento nativo (startSystemMove) compatible con Wayland y X11."""

    def __init__(self, ventana: QWidget, titulo: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.ventana = ventana
        self._origen_arrastre: Optional[QPoint] = None
        self.setObjectName("barraTitulo")
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(9)

        self.btn_cerrar = self._crear_boton(COLOR_CERRAR, ventana.close)
        self.btn_minimizar = self._crear_boton(COLOR_MINIMIZAR, ventana.showMinimized)
        self.btn_maximizar = self._crear_boton(COLOR_MAXIMIZAR, self.alternar_maximizado)
        for btn in (self.btn_cerrar, self.btn_minimizar, self.btn_maximizar):
            layout.addWidget(btn)
        layout.addStretch()

        self.lbl_titulo = QLabel(titulo, self)
        self.lbl_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_titulo.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: rgba(255, 255, 255, 0.85); background: transparent;"
        )
        layout.addWidget(self.lbl_titulo)
        layout.addStretch()

        # Contrapeso del ancho de los 3 botones para que el título quede centrado
        contrapeso = QWidget(self)
        contrapeso.setFixedWidth(3 * 13 + 2 * 9)
        contrapeso.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(contrapeso)

        self.actualizar_textos()

    def _crear_boton(self, color: str, accion) -> QPushButton:
        btn = QPushButton(self)
        btn.setFixedSize(13, 13)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet(
            f"QPushButton {{ background: {color}; border: none; border-radius: 6px; }}"
            "QPushButton:hover { border: 2px solid rgba(255, 255, 255, 0.48); }"
        )
        btn.clicked.connect(accion)
        return btn

    def actualizar_textos(self) -> None:
        """Refresca los tooltips (idioma y estado maximizado/restaurado)."""
        self.btn_cerrar.setToolTip(t("ventana.cerrar"))
        self.btn_minimizar.setToolTip(t("ventana.minimizar"))
        clave = "ventana.restaurar" if self.ventana.isMaximized() else "ventana.maximizar"
        self.btn_maximizar.setToolTip(t(clave))

    def alternar_maximizado(self) -> None:
        if self.ventana.isMaximized():
            self.ventana.showNormal()
        else:
            self.ventana.showMaximized()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.ventana.windowHandle()
            if handle is not None and handle.startSystemMove():
                self._origen_arrastre = None
                event.accept()
                return
            # Fallback manual si el compositor no soporta el movimiento nativo
            self._origen_arrastre = event.globalPosition().toPoint() - self.ventana.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._origen_arrastre is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self.ventana.isMaximized():
                self.ventana.showNormal()
            self.ventana.move(event.globalPosition().toPoint() - self._origen_arrastre)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._origen_arrastre = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.alternar_maximizado()
        super().mouseDoubleClickEvent(event)


class AsaRedimension(QWidget):
    """Franja invisible en un borde/esquina de la ventana sin marco que inicia el
    redimensionado nativo del sistema (startSystemResize)."""

    _CURSORES = {
        Qt.Edge.LeftEdge: Qt.CursorShape.SizeHorCursor,
        Qt.Edge.RightEdge: Qt.CursorShape.SizeHorCursor,
        Qt.Edge.TopEdge: Qt.CursorShape.SizeVerCursor,
        Qt.Edge.BottomEdge: Qt.CursorShape.SizeVerCursor,
        Qt.Edge.TopEdge | Qt.Edge.LeftEdge: Qt.CursorShape.SizeFDiagCursor,
        Qt.Edge.BottomEdge | Qt.Edge.RightEdge: Qt.CursorShape.SizeFDiagCursor,
        Qt.Edge.TopEdge | Qt.Edge.RightEdge: Qt.CursorShape.SizeBDiagCursor,
        Qt.Edge.BottomEdge | Qt.Edge.LeftEdge: Qt.CursorShape.SizeBDiagCursor,
    }

    def __init__(self, ventana: QWidget, bordes: Qt.Edge):
        super().__init__(ventana)
        self.ventana = ventana
        self.bordes = bordes
        self.setCursor(self._CURSORES[bordes])
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.ventana.windowHandle()
            if handle is not None and handle.startSystemResize(self.bordes):
                event.accept()
                return
        super().mousePressEvent(event)

    @staticmethod
    def crear_todas(ventana: QWidget) -> list["AsaRedimension"]:
        izq, der, arr, aba = Qt.Edge.LeftEdge, Qt.Edge.RightEdge, Qt.Edge.TopEdge, Qt.Edge.BottomEdge
        combinaciones = [izq, der, arr, aba, arr | izq, arr | der, aba | izq, aba | der]
        return [AsaRedimension(ventana, b) for b in combinaciones]

    def reposicionar(self) -> None:
        """Coloca el asa sobre su borde según el tamaño actual de la ventana."""
        w, h, g = self.ventana.width(), self.ventana.height(), GROSOR_BORDE
        izq = bool(self.bordes & Qt.Edge.LeftEdge)
        der = bool(self.bordes & Qt.Edge.RightEdge)
        arr = bool(self.bordes & Qt.Edge.TopEdge)
        aba = bool(self.bordes & Qt.Edge.BottomEdge)

        x = 0 if izq else (w - g if der else g)
        y = 0 if arr else (h - g if aba else g)
        ancho = g if (izq or der) else w - 2 * g
        alto = g if (arr or aba) else h - 2 * g
        self.setGeometry(x, y, ancho, alto)
        self.raise_()
