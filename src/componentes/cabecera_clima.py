from datetime import datetime
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.modelos.clima_datos import ReporteClimaCompleto
from src.servicios.i18n import t
from src.utils.fecha_utils import FechaHelper


class CabeceraClima(QWidget):
    """
    Componente superior estilo iOS que muestra:
    - Ciudad y País
    - Temperatura actual grande
    - Condición meteorológica y rango térmico diario
    - Píldoras dinámicas de fechas para los calendarios activados por el usuario
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config_calendarios: Optional[Dict[str, bool]] = None
        self._ultimo_dt: Optional[datetime] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Nombre de Ciudad
        self.lbl_ciudad = QLabel("--", self)
        self.lbl_ciudad.setObjectName("ciudadCabecera")
        self.lbl_ciudad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_ciudad)

        # 2. País / Región
        self.lbl_pais = QLabel("--", self)
        self.lbl_pais.setObjectName("paisCabecera")
        self.lbl_pais.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_pais)

        # 3. Temperatura Actual
        self.lbl_temperatura = QLabel("--°", self)
        self.lbl_temperatura.setObjectName("temperaturaCabecera")
        self.lbl_temperatura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_temperatura)

        # 4. Condición y Rango Térmico
        self.lbl_condicion = QLabel("--", self)
        self.lbl_condicion.setObjectName("condicionCabecera")
        self.lbl_condicion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_condicion)

        self.lbl_rango_hoy = QLabel(t("cabecera.hoy_rango", max="--", min="--"), self)
        self.lbl_rango_hoy.setObjectName("rangoHoyCabecera")
        self.lbl_rango_hoy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_rango_hoy)

        # 5. Contenedor de Píldoras de Fechas Dinámicas
        self.fechas_contenedor = QWidget(self)
        self.fechas_layout = QHBoxLayout(self.fechas_contenedor)
        self.fechas_layout.setContentsMargins(0, 8, 0, 0)
        self.fechas_layout.setSpacing(8)
        self.fechas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.fechas_contenedor)

        self.actualizar_fechas()

    def establecer_config_calendarios(self, config_calendarios: Optional[Dict[str, bool]]) -> None:
        """Actualiza la configuración de calendarios habilitados y reconstruye las píldoras."""
        self._config_calendarios = config_calendarios
        self.actualizar_fechas(self._ultimo_dt)

    def actualizar_fechas(self, dt: Optional[datetime] = None) -> None:
        """Reconstruye y actualiza las píldoras de fechas visibles según los calendarios activos."""
        self._ultimo_dt = dt

        # Limpiar píldoras previas
        while self.fechas_layout.count():
            item = self.fechas_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        pildoras = FechaHelper.obtener_pildoras_calendarios(dt, self._config_calendarios)
        for cal_id, icono, texto in pildoras:
            pildora = QFrame(self.fechas_contenedor)
            pildora.setObjectName("pildoraFecha")
            pildora_layout = QHBoxLayout(pildora)
            pildora_layout.setContentsMargins(10, 4, 10, 4)
            pildora_layout.setSpacing(4)

            lbl = QLabel(f"{icono} {texto}", pildora)
            lbl.setObjectName("textoPildoraFecha")
            pildora_layout.addWidget(lbl)
            self.fechas_layout.addWidget(pildora)

    def actualizar_datos(self, reporte: ReporteClimaCompleto) -> None:
        """Actualiza todos los elementos de la cabecera con el reporte de clima."""
        ub = reporte.ubicacion
        act = reporte.actual

        # Ciudad y País
        self.lbl_ciudad.setText(ub.ciudad)
        region_str = f"{ub.admin1}, " if ub.admin1 and ub.admin1 != ub.ciudad else ""
        self.lbl_pais.setText(f"{region_str}{ub.pais}")

        # Temperatura redondeada
        self.lbl_temperatura.setText(f"{round(act.temperatura)}°")

        # Condición
        self.lbl_condicion.setText(act.condicion.descripcion)

        # Rango hoy
        self.lbl_rango_hoy.setText(t("cabecera.hoy_rango", max=round(act.temp_max_hoy), min=round(act.temp_min_hoy)))

        # Actualizar fechas dinámicas
        self.actualizar_fechas()
