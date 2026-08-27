from typing import Optional

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from config import APP_NAME
from src.componentes.curva_horaria import EMOJIS_CLIMA
from src.modelos.clima_datos import ReporteClimaCompleto


class BandejaSistema(QSystemTrayIcon):
    """
    Icono en la bandeja del sistema (System Tray) para Linux.
    Renderiza dinámicamente un icono con la temperatura actual en tiempo real.
    """
    solicitar_mostrar_ocultar = Signal()
    solicitar_refresco = Signal()
    solicitar_salir = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._crear_icono_por_defecto()
        self._crear_menu()
        self.activated.connect(self._on_activated)

    def _crear_icono_por_defecto(self) -> None:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Fondo circular azul
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(48, 122, 178))
        painter.drawRoundedRect(QRectF(4, 4, 56, 56), 16, 16)

        # Emoji de sol
        font = QFont("sans-serif", 26)
        painter.setFont(font)
        painter.drawText(QRectF(0, 4, 64, 56), Qt.AlignmentFlag.AlignCenter, "🌤️")
        painter.end()

        self.setIcon(QIcon(pixmap))

    def _crear_menu(self) -> None:
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 40, 55, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 6px;
                color: #ffffff;
                font-family: -apple-system, Inter, sans-serif;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.15);
                margin: 4px 8px;
            }
        """)

        from src.servicios.i18n import t

        self.action_header = QAction(f"🌤️ {t('app.nombre')}", self.menu)
        self.action_header.setEnabled(False)
        self.menu.addAction(self.action_header)
        self.menu.addSeparator()

        self.action_toggle = QAction(f"{t('bandeja.mostrar')} / {t('bandeja.ocultar')}", self.menu)
        self.action_toggle.triggered.connect(self.solicitar_mostrar_ocultar.emit)
        self.menu.addAction(self.action_toggle)

        self.action_refrescar = QAction(f"🔄 {t('bandeja.refrescar')}", self.menu)
        self.action_refrescar.triggered.connect(self.solicitar_refresco.emit)
        self.menu.addAction(self.action_refrescar)

        self.menu.addSeparator()

        self.action_salir = QAction(f"✕ {t('bandeja.salir')}", self.menu)
        self.action_salir.triggered.connect(self.solicitar_salir.emit)
        self.menu.addAction(self.action_salir)

        self.setContextMenu(self.menu)

    def actualizar_clima_tray(self, reporte: ReporteClimaCompleto) -> None:
        """Genera un icono dinámico con el emoji y la temperatura en vivo."""
        act = reporte.actual
        ub = reporte.ubicacion
        emoji = EMOJIS_CLIMA.get(act.condicion.icon_name, "🌤️")
        temp_str = f"{round(act.temperatura)}°"

        # Crear pixmap de 64x64
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Fondo redondeado
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(35, 45, 60, 230))
        painter.drawRoundedRect(QRectF(2, 2, 60, 60), 16, 16)

        # Emoji superior
        font_emoji = QFont("sans-serif", 16)
        painter.setFont(font_emoji)
        painter.drawText(QRectF(0, 6, 64, 26), Qt.AlignmentFlag.AlignCenter, emoji)

        # Temperatura inferior
        font_temp = QFont("-apple-system, Inter, sans-serif", 15, QFont.Weight.Bold)
        painter.setFont(font_temp)
        painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(QRectF(0, 32, 64, 26), Qt.AlignmentFlag.AlignCenter, temp_str)

        painter.end()

        self.setIcon(QIcon(pixmap))
        self.setToolTip(f"{APP_NAME} - {ub.ciudad} ({temp_str}, {act.condicion.descripcion})")
        self.action_header.setText(f"📍 {ub.ciudad} • {temp_str} ({act.condicion.descripcion})")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in [QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick]:
            self.solicitar_mostrar_ocultar.emit()

    def mostrar_alerta(self, titulo: str, mensaje: str, icon_tipo: str = "info") -> None:
        """Muestra una notificación nativa del sistema en Linux / Desktop."""
        if not self.isVisible():
            return

        icon = QSystemTrayIcon.MessageIcon.Information
        if icon_tipo == "warning":
            icon = QSystemTrayIcon.MessageIcon.Warning
        elif icon_tipo == "critical":
            icon = QSystemTrayIcon.MessageIcon.Critical

        self.showMessage(titulo, mensaje, icon, 6000)

