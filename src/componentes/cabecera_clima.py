from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.modelos.clima_datos import ReporteClimaCompleto
from src.utils.fecha_utils import FechaHelper


class CabeceraClima(QWidget):
    """
    Cabecera visual principal con nombre de ciudad, temperatura prominente estilo Apple,
    condición climática, rango térmico del día y píldoras con fechas duales.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 15)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Ciudad y País
        self.lbl_ciudad = QLabel("Cargando...", self)
        self.lbl_ciudad.setObjectName("ciudadCabecera")
        self.lbl_ciudad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_ciudad)

        self.lbl_pais = QLabel("", self)
        self.lbl_pais.setObjectName("paisCabecera")
        self.lbl_pais.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_pais)

        # 2. Temperatura Gigante
        self.lbl_temperatura = QLabel("--°", self)
        self.lbl_temperatura.setObjectName("temperaturaGigante")
        self.lbl_temperatura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_temperatura)

        # 3. Condición Climática
        self.lbl_condicion = QLabel("Obteniendo pronóstico...", self)
        self.lbl_condicion.setObjectName("condicionCabecera")
        self.lbl_condicion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_condicion)

        # 4. Rango Térmico de Hoy (Máx / Mín)
        self.lbl_rango_hoy = QLabel("Máx: --°  •  Mín: --°", self)
        self.lbl_rango_hoy.setObjectName("rangoHoyCabecera")
        self.lbl_rango_hoy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_rango_hoy)

        # 5. Píldoras de Fechas Duales
        fechas_layout = QHBoxLayout()
        fechas_layout.setContentsMargins(0, 12, 0, 0)
        fechas_layout.setSpacing(10)
        fechas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Píldora Gregoriana
        pildora_greg = QFrame(self)
        pildora_greg.setObjectName("pildoraFecha")
        pildora_greg_layout = QHBoxLayout(pildora_greg)
        pildora_greg_layout.setContentsMargins(10, 4, 10, 4)
        self.lbl_fecha_greg = QLabel("📅 --", pildora_greg)
        self.lbl_fecha_greg.setObjectName("textoPildoraFecha")
        pildora_greg_layout.addWidget(self.lbl_fecha_greg)
        fechas_layout.addWidget(pildora_greg)

        # Píldora Hijri
        pildora_hijri = QFrame(self)
        pildora_hijri.setObjectName("pildoraFecha")
        pildora_hijri_layout = QHBoxLayout(pildora_hijri)
        pildora_hijri_layout.setContentsMargins(10, 4, 10, 4)
        self.lbl_fecha_hijri = QLabel("🌙 --", pildora_hijri)
        self.lbl_fecha_hijri.setObjectName("textoPildoraFecha")
        pildora_hijri_layout.addWidget(self.lbl_fecha_hijri)
        fechas_layout.addWidget(pildora_hijri)

        layout.addLayout(fechas_layout)

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
        self.lbl_rango_hoy.setText(f"Máx: {round(act.temp_max_hoy)}°  •  Mín: {round(act.temp_min_hoy)}°")

        # Fechas
        greg_str, hijri_str = FechaHelper.fecha_dual_completa()
        self.lbl_fecha_greg.setText(f"📅 {greg_str}")
        self.lbl_fecha_hijri.setText(f"🌙 {hijri_str}")

