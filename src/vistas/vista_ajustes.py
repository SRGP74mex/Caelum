from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.servicios.config_manager import ConfigManager

UNIDADES_TEMPERATURA = [("Celsius (°C)", "celsius"), ("Fahrenheit (°F)", "fahrenheit")]
UNIDADES_VIENTO = [("km/h", "kmh"), ("m/s", "ms"), ("mph", "mph")]


class VistaAjustes(QDialog):
    """Diálogo modal de preferencias: unidades y comportamiento de la bandeja del
    sistema. Reutiliza la instancia de ConfigManager ya creada en VentanaPrincipal
    en vez de abrir una segunda, para no leer/escribir el JSON de config dos veces."""

    ajustes_guardados = Signal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Ajustes")
        self.setMinimumWidth(320)
        self._init_ui()
        self._cargar_valores_actuales()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)

        titulo = QLabel("⚙️ Ajustes", self)
        titulo.setStyleSheet("font-size: 18px; font-weight: 600; color: #ffffff;")
        layout.addWidget(titulo)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_temperatura = QComboBox(self)
        for etiqueta, valor in UNIDADES_TEMPERATURA:
            self.combo_temperatura.addItem(etiqueta, valor)
        form.addRow("Temperatura:", self.combo_temperatura)

        self.combo_viento = QComboBox(self)
        for etiqueta, valor in UNIDADES_VIENTO:
            self.combo_viento.addItem(etiqueta, valor)
        form.addRow("Velocidad del viento:", self.combo_viento)

        layout.addLayout(form)

        self.chk_mostrar_bandeja = QCheckBox("Mostrar icono en la bandeja del sistema", self)
        layout.addWidget(self.chk_mostrar_bandeja)

        self.chk_cerrar_a_bandeja = QCheckBox("Al cerrar la ventana, minimizar a la bandeja", self)
        layout.addWidget(self.chk_cerrar_a_bandeja)

        botones = QHBoxLayout()
        botones.addStretch()
        self.btn_cancelar = QPushButton("Cancelar", self)
        self.btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton("Guardar", self)
        self.btn_guardar.setDefault(True)
        self.btn_guardar.clicked.connect(self._guardar)
        botones.addWidget(self.btn_guardar)

        layout.addLayout(botones)

    def _cargar_valores_actuales(self) -> None:
        unidades = self.config_manager.datos.get("unidades", {})
        idx_temp = self.combo_temperatura.findData(unidades.get("temperatura", "celsius"))
        self.combo_temperatura.setCurrentIndex(max(idx_temp, 0))

        idx_viento = self.combo_viento.findData(unidades.get("viento", "kmh"))
        self.combo_viento.setCurrentIndex(max(idx_viento, 0))

        self.chk_mostrar_bandeja.setChecked(bool(self.config_manager.datos.get("mostrar_bandeja", True)))
        self.chk_cerrar_a_bandeja.setChecked(bool(self.config_manager.datos.get("cerrar_a_bandeja", False)))

    def _guardar(self) -> None:
        unidades = {
            "temperatura": self.combo_temperatura.currentData(),
            "viento": self.combo_viento.currentData(),
        }
        self.config_manager.guardar_preferencias(
            unidades=unidades,
            mostrar_bandeja=self.chk_mostrar_bandeja.isChecked(),
            cerrar_a_bandeja=self.chk_cerrar_a_bandeja.isChecked(),
        )

        self.ajustes_guardados.emit()
        self.accept()
