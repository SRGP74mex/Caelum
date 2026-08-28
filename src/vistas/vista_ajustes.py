from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import IDIOMAS_SOPORTADOS
from src.servicios.config_manager import ConfigManager
from src.servicios.i18n import establecer_idioma, t

UNIDADES_TEMPERATURA = [("Celsius (°C)", "celsius"), ("Fahrenheit (°F)", "fahrenheit")]
UNIDADES_VIENTO = [("km/h", "kmh"), ("m/s", "ms"), ("mph", "mph")]


class VistaAjustes(QDialog):
    """
    Diálogo modal de preferencias con estilo Glassmorphism oscuro:
    - Selector de Idioma (Español, English, Français, Italiano, Deutsch, 日本語).
    - Selector de Calendarios Visibles (Gregoriano, Hijri, Hebreo, Jalali, Budista, Etíope, Saka, Chino).
    - Unidades de medida (temperatura, viento).
    - Bandeja del sistema y notificaciones meteorológicas inteligentes.
    """
    ajustes_guardados = Signal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle(f"{t('ajustes.titulo')} - WeatherApp Linux")
        self.setMinimumWidth(460)
        self._aplicar_estilos()
        self._init_ui()
        self._cargar_valores_actuales()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #1a2230;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 14px;
                color: #ffffff;
                font-family: -apple-system, Inter, "Segoe UI", sans-serif;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QLabel#seccion_titulo {
                font-size: 14px;
                font-weight: 700;
                color: #93c5fd;
                margin-top: 6px;
                margin-bottom: 2px;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 8px;
                padding: 6px 12px;
                color: #ffffff;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox:hover {
                background-color: rgba(255, 255, 255, 0.16);
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 8px;
                color: #ffffff;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                padding: 4px;
            }
            QCheckBox {
                color: #e2e8f0;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.30);
                background-color: rgba(255, 255, 255, 0.08);
            }
            QCheckBox::indicator:hover {
                border: 1px solid rgba(255, 255, 255, 0.50);
                background-color: rgba(255, 255, 255, 0.14);
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border: 1px solid #60a5fa;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 8px;
                padding: 8px 18px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.20);
                border: 1px solid rgba(255, 255, 255, 0.40);
            }
            QPushButton#btn_guardar {
                background-color: #2563eb;
                border: 1px solid #3b82f6;
                font-weight: 600;
            }
            QPushButton#btn_guardar:hover {
                background-color: #1d4ed8;
            }
            QFrame#separador {
                background-color: rgba(255, 255, 255, 0.10);
                max-height: 1px;
                margin-top: 4px;
                margin-bottom: 4px;
            }
        """)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)

        titulo = QLabel(f"⚙️ {t('ajustes.titulo')}", self)
        titulo.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff; margin-bottom: 4px;")
        layout.addWidget(titulo)

        # 1. Sección Idioma & Unidades
        lbl_sec_general = QLabel(f"🌍 {t('ajustes.pestana_general').upper()} & {t('ajustes.pestana_unidades').upper()}", self)
        lbl_sec_general.setObjectName("seccion_titulo")
        layout.addWidget(lbl_sec_general)

        form = QFormLayout()
        form.setSpacing(8)

        # Selector de Idioma
        self.combo_idioma = QComboBox(self)
        for codigo, nombre in IDIOMAS_SOPORTADOS.items():
            self.combo_idioma.addItem(nombre, codigo)
        form.addRow(f"{t('ajustes.idioma')}:", self.combo_idioma)

        # Selector de Temperatura
        self.combo_temperatura = QComboBox(self)
        for etiqueta, valor in UNIDADES_TEMPERATURA:
            self.combo_temperatura.addItem(etiqueta, valor)
        form.addRow(f"{t('ajustes.temperatura')}:", self.combo_temperatura)

        # Selector de Viento
        self.combo_viento = QComboBox(self)
        for etiqueta, valor in UNIDADES_VIENTO:
            self.combo_viento.addItem(etiqueta, valor)
        form.addRow(f"{t('ajustes.viento')}:", self.combo_viento)

        layout.addLayout(form)

        # Separador 1
        sep1 = QFrame(self)
        sep1.setObjectName("separador")
        sep1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep1)

        # 2. Sección Calendarios Visibles
        lbl_sec_cal = QLabel(f"📅 {t('ajustes.calendarios_titulo').upper()}", self)
        lbl_sec_cal.setObjectName("seccion_titulo")
        layout.addWidget(lbl_sec_cal)

        grid_cal = QGridLayout()
        grid_cal.setSpacing(8)

        self.chk_cal_gregoriano = QCheckBox(f"📅 {t('ajustes.cal_gregoriano')}", self)
        self.chk_cal_hijri = QCheckBox(f"🌙 {t('ajustes.cal_hijri')}", self)
        self.chk_cal_hebreo = QCheckBox(f"🕎 {t('ajustes.cal_hebreo')}", self)
        self.chk_cal_jalali = QCheckBox(f"☀️ {t('ajustes.cal_jalali')}", self)
        self.chk_cal_budista = QCheckBox(f"☸️ {t('ajustes.cal_budista')}", self)
        self.chk_cal_etiope = QCheckBox(f"🇪🇹 {t('ajustes.cal_etiope')}", self)
        self.chk_cal_saka = QCheckBox(f"🇮🇳 {t('ajustes.cal_saka')}", self)
        self.chk_cal_chino = QCheckBox(f"🐉 {t('ajustes.cal_chino')}", self)

        grid_cal.addWidget(self.chk_cal_gregoriano, 0, 0)
        grid_cal.addWidget(self.chk_cal_hijri, 0, 1)
        grid_cal.addWidget(self.chk_cal_hebreo, 1, 0)
        grid_cal.addWidget(self.chk_cal_jalali, 1, 1)
        grid_cal.addWidget(self.chk_cal_budista, 2, 0)
        grid_cal.addWidget(self.chk_cal_etiope, 2, 1)
        grid_cal.addWidget(self.chk_cal_saka, 3, 0)
        grid_cal.addWidget(self.chk_cal_chino, 3, 1)

        layout.addLayout(grid_cal)

        # Separador 2
        sep2 = QFrame(self)
        sep2.setObjectName("separador")
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        # 3. Sección Bandeja & Notificaciones
        lbl_sec_bandeja = QLabel(f"🖥️ {t('ajustes.bandeja').upper()} & 🔔 {t('ajustes.pestana_notificaciones').upper()}", self)
        lbl_sec_bandeja.setObjectName("seccion_titulo")
        layout.addWidget(lbl_sec_bandeja)

        self.chk_mostrar_bandeja = QCheckBox(t("ajustes.mostrar_bandeja"), self)
        layout.addWidget(self.chk_mostrar_bandeja)

        self.chk_cerrar_a_bandeja = QCheckBox(t("ajustes.cerrar_a_bandeja"), self)
        layout.addWidget(self.chk_cerrar_a_bandeja)

        self.chk_notif_activadas = QCheckBox(t("ajustes.activar_notificaciones"), self)
        self.chk_notif_activadas.toggled.connect(self._on_notif_toggled)
        layout.addWidget(self.chk_notif_activadas)

        notif_row = QHBoxLayout()
        notif_row.setSpacing(12)
        self.chk_alerta_lluvia = QCheckBox(t("ajustes.alerta_lluvia"), self)
        self.chk_alerta_tormenta = QCheckBox(t("ajustes.alerta_tormenta"), self)
        self.chk_alerta_atardecer = QCheckBox(t("ajustes.alerta_atardecer"), self)
        notif_row.addWidget(self.chk_alerta_lluvia)
        notif_row.addWidget(self.chk_alerta_tormenta)
        notif_row.addWidget(self.chk_alerta_atardecer)
        layout.addLayout(notif_row)

        layout.addSpacing(6)

        from src.utils.entorno_sistema import EntornoSistema
        servidor = EntornoSistema.obtener_servidor_grafico()
        escritorio = EntornoSistema.obtener_entorno_escritorio()

        # Botones y pie informativo
        botones = QHBoxLayout()
        lbl_entorno = QLabel(f"🐧 {servidor} • {escritorio}", self)
        lbl_entorno.setStyleSheet("color: rgba(255, 255, 255, 0.45); font-size: 11px;")
        botones.addWidget(lbl_entorno)
        botones.addStretch()

        self.btn_cancelar = QPushButton(t("ajustes.cancelar"), self)
        self.btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton(t("ajustes.guardar"), self)
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setDefault(True)
        self.btn_guardar.clicked.connect(self._guardar)
        botones.addWidget(self.btn_guardar)

        layout.addLayout(botones)

    def _on_notif_toggled(self, checked: bool) -> None:
        self.chk_alerta_lluvia.setEnabled(checked)
        self.chk_alerta_tormenta.setEnabled(checked)
        self.chk_alerta_atardecer.setEnabled(checked)

    def _cargar_valores_actuales(self) -> None:
        # Idioma
        idioma_actual = self.config_manager.datos.get("idioma", "auto")
        idx_lang = self.combo_idioma.findData(idioma_actual)
        self.combo_idioma.setCurrentIndex(max(idx_lang, 0))

        # Unidades
        unidades = self.config_manager.datos.get("unidades", {})
        idx_temp = self.combo_temperatura.findData(unidades.get("temperatura", "celsius"))
        self.combo_temperatura.setCurrentIndex(max(idx_temp, 0))

        idx_viento = self.combo_viento.findData(unidades.get("viento", "kmh"))
        self.combo_viento.setCurrentIndex(max(idx_viento, 0))

        # Calendarios
        cal_cfg = self.config_manager.obtener_calendarios_activos()
        self.chk_cal_gregoriano.setChecked(bool(cal_cfg.get("gregoriano", True)))
        self.chk_cal_hijri.setChecked(bool(cal_cfg.get("hijri", True)))
        self.chk_cal_hebreo.setChecked(bool(cal_cfg.get("hebreo", True)))
        self.chk_cal_jalali.setChecked(bool(cal_cfg.get("jalali", False)))
        self.chk_cal_budista.setChecked(bool(cal_cfg.get("budista", False)))
        self.chk_cal_etiope.setChecked(bool(cal_cfg.get("etiope", False)))
        self.chk_cal_saka.setChecked(bool(cal_cfg.get("saka", False)))
        self.chk_cal_chino.setChecked(bool(cal_cfg.get("chino", False)))

        # Bandeja
        self.chk_mostrar_bandeja.setChecked(bool(self.config_manager.datos.get("mostrar_bandeja", True)))
        self.chk_cerrar_a_bandeja.setChecked(bool(self.config_manager.datos.get("cerrar_a_bandeja", False)))

        # Notificaciones
        notif = self.config_manager.datos.get("notificaciones", {})
        activadas = bool(notif.get("activadas", True))
        self.chk_notif_activadas.setChecked(activadas)
        self.chk_alerta_lluvia.setChecked(bool(notif.get("alerta_lluvia", True)))
        self.chk_alerta_tormenta.setChecked(bool(notif.get("alerta_tormenta", True)))
        self.chk_alerta_atardecer.setChecked(bool(notif.get("alerta_atardecer", False)))
        self._on_notif_toggled(activadas)

    def _guardar(self) -> None:
        idioma = self.combo_idioma.currentData()
        establecer_idioma(idioma)

        unidades = {
            "temperatura": self.combo_temperatura.currentData(),
            "viento": self.combo_viento.currentData(),
        }
        calendarios = {
            "gregoriano": self.chk_cal_gregoriano.isChecked(),
            "hijri": self.chk_cal_hijri.isChecked(),
            "hebreo": self.chk_cal_hebreo.isChecked(),
            "jalali": self.chk_cal_jalali.isChecked(),
            "budista": self.chk_cal_budista.isChecked(),
            "etiope": self.chk_cal_etiope.isChecked(),
            "saka": self.chk_cal_saka.isChecked(),
            "chino": self.chk_cal_chino.isChecked(),
        }
        notificaciones = {
            "activadas": self.chk_notif_activadas.isChecked(),
            "alerta_lluvia": self.chk_alerta_lluvia.isChecked(),
            "alerta_tormenta": self.chk_alerta_tormenta.isChecked(),
            "alerta_atardecer": self.chk_alerta_atardecer.isChecked(),
        }
        self.config_manager.guardar_preferencias(
            unidades=unidades,
            mostrar_bandeja=self.chk_mostrar_bandeja.isChecked(),
            cerrar_a_bandeja=self.chk_cerrar_a_bandeja.isChecked(),
            notificaciones=notificaciones,
            idioma=idioma,
            calendarios=calendarios
        )

        self.ajustes_guardados.emit()
        self.accept()
