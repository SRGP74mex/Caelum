from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TarjetaBento(QFrame):
    """
    Tarjeta base con efecto Glassmorphism y cabecera modular con icono y título.
    """
    def __init__(self, titulo: str = "", icono: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "tarjetaBento")
        self.setObjectName("tarjetaBento")

        # Sombra suave
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(24)
        sombra.setColor(QColor(0, 0, 0, 45))
        sombra.setOffset(0, 8)
        self.setGraphicsEffect(sombra)

        # Layout Principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 14, 16, 16)
        self.main_layout.setSpacing(10)

        # Encabezado si se especifica título o icono
        if titulo or icono:
            self.header_layout = QHBoxLayout()
            self.header_layout.setContentsMargins(0, 0, 0, 0)
            self.header_layout.setSpacing(6)

            if icono:
                self.lbl_icono = QLabel(icono, self)
                self.lbl_icono.setObjectName("iconoBento")
                self.header_layout.addWidget(self.lbl_icono)

            if titulo:
                self.lbl_titulo = QLabel(titulo.upper(), self)
                self.lbl_titulo.setObjectName("tituloBento")
                self.header_layout.addWidget(self.lbl_titulo)

            self.header_layout.addStretch()
            self.main_layout.addLayout(self.header_layout)

        # Contenedor de contenido
        self.contenido_widget = QWidget(self)
        self.contenido_layout = QVBoxLayout(self.contenido_widget)
        self.contenido_layout.setContentsMargins(0, 0, 0, 0)
        self.contenido_layout.setSpacing(8)
        self.main_layout.addWidget(self.contenido_widget)

    def agregar_contenido(self, widget: QWidget) -> None:
        """Agrega un widget al layout interno de la tarjeta."""
        self.contenido_layout.addWidget(widget)

    def limpiar_contenido(self) -> None:
        """Elimina los widgets del layout interno."""
        while self.contenido_layout.count():
            item = self.contenido_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

