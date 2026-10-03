from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.modelos.clima_datos import ReporteClimaCompleto
from src.servicios.i18n import t


@dataclass
class AlertaClimaInfo:
    tipo: str        # "lluvia_torrencial", "calor_extremo", "tormenta_granizo", "viento_fuerte", "uv_extremo"
    nivel: str       # "critica", "advertencia", "aviso"
    icono: str
    titulo: str
    descripcion: str
    color_fondo: str
    color_borde: str
    color_texto: str


class BannerAlertaWidget(QWidget):
    """
    Banner visual para alertas meteorológicas críticas (inundaciones, lluvias torrenciales,
    olas de calor extremo, tormentas severas con granizo y vendavales).
    """
    cerrar_alerta = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.alerta_activa: Optional[AlertaClimaInfo] = None
        self._init_ui()
        self.hide()

    def _init_ui(self) -> None:
        self.layout_principal = QHBoxLayout(self)
        self.layout_principal.setContentsMargins(14, 10, 14, 10)
        self.layout_principal.setSpacing(12)

        self.lbl_icono = QLabel("🚨", self)
        self.lbl_icono.setStyleSheet("font-size: 24px;")
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_principal.addWidget(self.lbl_icono)

        v_texto = QVBoxLayout()
        v_texto.setContentsMargins(0, 0, 0, 0)
        v_texto.setSpacing(2)

        self.lbl_titulo = QLabel(t("alertas.banner_titulo"), self)
        self.lbl_titulo.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        v_texto.addWidget(self.lbl_titulo)

        self.lbl_desc = QLabel("", self)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.90);")
        v_texto.addWidget(self.lbl_desc)

        self.layout_principal.addLayout(v_texto, stretch=1)

        self.btn_cerrar = QPushButton("✕", self)
        self.btn_cerrar.setFixedSize(24, 24)
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 12px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.30);
            }
        """)
        self.btn_cerrar.clicked.connect(self.hide)
        self.layout_principal.addWidget(self.btn_cerrar, alignment=Qt.AlignmentFlag.AlignTop)

    def evaluar_alertas(self, reporte: ReporteClimaCompleto) -> Optional[AlertaClimaInfo]:
        """Analiza el reporte actual y pronóstico 24h/7d para detectar riesgos climáticos."""
        act = reporte.actual

        # 1. Alerta de Lluvia Torrencial / Riesgo de Inundación
        precip_hoy = reporte.dias_7d[0].precipitacion_total_mm if reporte.dias_7d else act.precipitacion_mm
        max_precip_hora = max((h.precipitacion_mm for h in reporte.horas_24h[:6]), default=0.0) if reporte.horas_24h else 0.0

        if max_precip_hora >= 12.0 or precip_hoy >= 30.0:
            return AlertaClimaInfo(
                tipo="lluvia_torrencial",
                nivel="critica",
                icono="🌊",
                titulo=t("alertas.inundacion_titulo"),
                descripcion=t("alertas.inundacion_desc", mm=f"{precip_hoy:.1f}"),
                color_fondo="rgba(220, 38, 38, 0.28)",
                color_borde="rgba(239, 68, 68, 0.65)",
                color_texto="#fca5a5"
            )

        # 2. Alerta de Ola de Calor Extremo
        temp_max_hoy = reporte.dias_7d[0].temp_max if reporte.dias_7d else act.temp_max_hoy
        if temp_max_hoy >= 38.0 or act.sensacion_termica >= 40.0:
            return AlertaClimaInfo(
                tipo="calor_extremo",
                nivel="critica",
                icono="🔥",
                titulo=t("alertas.calor_titulo"),
                descripcion=t("alertas.calor_desc", temp=round(temp_max_hoy), sens=round(act.sensacion_termica)),
                color_fondo="rgba(234, 88, 12, 0.28)",
                color_borde="rgba(249, 115, 22, 0.65)",
                color_texto="#fed7aa"
            )

        # 3. Alerta de Tormenta Eléctrica Severa con Granizo
        if act.condicion.wmo_code in [96, 99]:
            return AlertaClimaInfo(
                tipo="tormenta_granizo",
                nivel="critica",
                icono="⛈️",
                titulo=t("alertas.tormenta_titulo"),
                descripcion=t("alertas.tormenta_desc"),
                color_fondo="rgba(147, 51, 234, 0.28)",
                color_borde="rgba(168, 85, 247, 0.65)",
                color_texto="#e9d5ff"
            )

        # 4. Alerta de Vendaval / Viento Violento
        if act.viento_rafagas and act.viento_rafagas >= 70.0:
            return AlertaClimaInfo(
                tipo="viento_fuerte",
                nivel="advertencia",
                icono="💨",
                titulo=t("alertas.viento_titulo"),
                descripcion=t("alertas.viento_desc", vel=f"{round(act.viento_rafagas)} km/h"),
                color_fondo="rgba(217, 119, 6, 0.26)",
                color_borde="rgba(245, 158, 11, 0.60)",
                color_texto="#fef3c7"
            )

        # 5. Radiación UV Extrema
        if act.indice_uv >= 10.0:
            return AlertaClimaInfo(
                tipo="uv_extremo",
                nivel="advertencia",
                icono="☀️",
                titulo=t("alertas.uv_titulo"),
                descripcion=t("alertas.uv_desc", uv=f"{act.indice_uv:.0f}"),
                color_fondo="rgba(225, 29, 72, 0.24)",
                color_borde="rgba(244, 63, 94, 0.55)",
                color_texto="#fecdd3"
            )

        return None

    def actualizar_alerta(self, reporte: ReporteClimaCompleto) -> None:
        alerta = self.evaluar_alertas(reporte)
        self.alerta_activa = alerta

        if alerta:
            self.lbl_icono.setText(alerta.icono)
            self.lbl_titulo.setText(alerta.titulo)
            self.lbl_desc.setText(alerta.descripcion)
            self.setStyleSheet(f"""
                BannerAlertaWidget {{
                    background-color: {alerta.color_fondo};
                    border: 1px solid {alerta.color_borde};
                    border-radius: 12px;
                }}
            """)
            self.show()
        else:
            self.hide()

