from typing import List, Optional

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.modelos.clima_datos import Ubicacion
from src.servicios.config_manager import ConfigManager
from src.servicios.geocoding_service import GeocodingService
from src.servicios.i18n import t
from src.servicios.worker import ejecutar_en_segundo_plano


class InputBusqueda(QLineEdit):
    """QLineEdit con soporte para capturar teclas de navegación y foco."""
    flecha_abajo_presionada = Signal()
    flecha_arriba_presionada = Signal()
    escape_presionado = Signal()
    foco_ganado = Signal()
    foco_perdido = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Down:
            self.flecha_abajo_presionada.emit()
            return
        elif event.key() == Qt.Key.Key_Up:
            self.flecha_arriba_presionada.emit()
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.escape_presionado.emit()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.foco_ganado.emit()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        self.foco_perdido.emit()


class BarraBusqueda(QWidget):
    """
    Barra de búsqueda reactiva con sugerencias flotantes tipo Pop-up / Overlay (Z-Index superior):
    - Flota por encima de las tarjetas sin desplazar ni mover el contenido de la interfaz.
    - No secuestra el foco de teclado, permitiendo escribir fluidamente sin interrupciones.
    - Al hacer foco sin texto, sugiere la ubicación detectada por IP y ciudades recientes.
    - Al escribir, busca en tiempo real en todo el mundo con respuesta instantánea y caché.
    - Soporte completo para navegación por teclado (flechas, Enter, Esc) y ratón.
    """
    ciudad_seleccionada = Signal(Ubicacion)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.geo_service = GeocodingService()
        self.config_manager = ConfigManager()
        self.resultados_actuales: List[Ubicacion] = []
        self._search_id = 0
        self._ciudades_cercanas_cache: List[Ubicacion] = []

        # Temporizador para debounce de búsqueda suave (320 ms)
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._realizar_busqueda)

        self._init_ui()
        self._precargar_ciudades_cercanas()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Contenedor de la barra
        self.contenedor = QFrame(self)
        self.contenedor.setObjectName("contenedorBusqueda")
        bar_layout = QHBoxLayout(self.contenedor)
        bar_layout.setContentsMargins(12, 6, 8, 6)
        bar_layout.setSpacing(8)

        # Icono de lupa
        lbl_icono = QLabel("🔍", self.contenedor)
        lbl_icono.setStyleSheet("font-size: 14px; background: transparent;")
        bar_layout.addWidget(lbl_icono)

        # Input de texto con interceptor de teclas y foco
        self.input_busqueda = InputBusqueda(self.contenedor)
        self.input_busqueda.setObjectName("inputBusqueda")
        self.input_busqueda.setPlaceholderText(t("busqueda.placeholder"))
        self.input_busqueda.textChanged.connect(self._on_text_changed)
        self.input_busqueda.returnPressed.connect(self._on_enter_pressed)
        self.input_busqueda.flecha_abajo_presionada.connect(self._on_flecha_abajo)
        self.input_busqueda.flecha_arriba_presionada.connect(self._on_flecha_arriba)
        self.input_busqueda.escape_presionado.connect(self.limpiar)
        self.input_busqueda.foco_ganado.connect(self._on_foco_ganado)
        self.input_busqueda.foco_perdido.connect(self._on_foco_perdido)
        bar_layout.addWidget(self.input_busqueda)

        # Botón limpiar
        self.btn_limpiar = QPushButton("✕", self.contenedor)
        self.btn_limpiar.setObjectName("botonLimpiarBusqueda")
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.setVisible(False)
        self.btn_limpiar.clicked.connect(self.limpiar)
        bar_layout.addWidget(self.btn_limpiar)

        main_layout.addWidget(self.contenedor)

        # Lista de sugerencias desplegable flotante (Overlay / Z-Index)
        # Se configura con ToolTip y WindowDoesNotAcceptFocus para flotar por encima sin robar el teclado
        self.lista_sugerencias = QListWidget()
        self.lista_sugerencias.setObjectName("listaSugerencias")
        self.lista_sugerencias.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.lista_sugerencias.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.lista_sugerencias.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.lista_sugerencias.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lista_sugerencias.itemClicked.connect(self._on_item_clicked)

    def _posicionar_y_mostrar_sugerencias(self) -> None:
        """Posiciona la lista flotante directamente bajo la barra de búsqueda en coordenadas globales."""
        if self.lista_sugerencias.count() == 0 or not self.isVisible():
            self.lista_sugerencias.hide()
            return

        pos_global = self.contenedor.mapToGlobal(QPoint(0, self.contenedor.height() + 4))
        ancho = self.contenedor.width()
        num_items = min(self.lista_sugerencias.count(), 6)
        altura = min(num_items * 38 + 14, 240)

        self.lista_sugerencias.setGeometry(pos_global.x(), pos_global.y(), ancho, altura)
        self.lista_sugerencias.show()
        self.lista_sugerencias.raise_()

    def _precargar_ciudades_cercanas(self) -> None:
        """Detecta la IP y precarga ciudades en segundo plano sin bloquear."""
        def _detect():
            ub_ip = self.geo_service.detectar_ubicacion_ip()
            return [ub_ip]

        def _on_result(ciudades: List[Ubicacion]):
            self._ciudades_cercanas_cache = ciudades

        ejecutar_en_segundo_plano(_detect, on_result=_on_result)

    def _on_foco_ganado(self) -> None:
        """Al hacer clic en la barra vacía, muestra sugerencias dinámicas (GeoIP y recientes)."""
        if not self.input_busqueda.text().strip():
            self._mostrar_sugerencias_dinamicas()

    def _on_foco_perdido(self) -> None:
        """Oculta las sugerencias si el foco se mueve a otro control."""
        QTimer.singleShot(250, self._verificar_cerrar_popup)

    def _verificar_cerrar_popup(self) -> None:
        if not self.input_busqueda.hasFocus():
            self.lista_sugerencias.hide()

    def _mostrar_sugerencias_dinamicas(self) -> None:
        self.lista_sugerencias.clear()
        self.resultados_actuales = []

        recientes = self.config_manager.obtener_ciudades_recientes()
        candidatos = []

        from src.servicios.i18n import t

        # 1. Ciudades del historial reciente
        if recientes:
            for r in recientes[:4]:
                candidatos.append((r, t("busqueda.reciente")))

        # 2. Ciudades cercanas / IP
        if self._ciudades_cercanas_cache:
            for c in self._ciudades_cercanas_cache:
                if not any(cand[0].latitud == c.latitud and cand[0].longitud == c.longitud for cand in candidatos):
                    tag = t("busqueda.mi_ubicacion") if len(candidatos) == 0 else t("busqueda.cercana")
                    candidatos.append((c, tag))

        if not candidatos:
            self.lista_sugerencias.hide()
            return

        for ub, etiqueta in candidatos[:6]:
            self.resultados_actuales.append(ub)
            region_str = f" ({ub.admin1})" if ub.admin1 and ub.admin1 != ub.ciudad else ""
            item_text = f"{etiqueta}: {ub.ciudad}{region_str}, {ub.pais}"
            item = QListWidgetItem(item_text)
            self.lista_sugerencias.addItem(item)

        self.lista_sugerencias.setCurrentRow(0)
        self._posicionar_y_mostrar_sugerencias()

    def _on_text_changed(self, texto: str) -> None:
        self.btn_limpiar.setVisible(bool(texto))
        query = texto.strip()
        if len(query) >= 2:
            self.debounce_timer.start(320)
        elif len(query) == 0:
            self.debounce_timer.stop()
            self._mostrar_sugerencias_dinamicas()
        else:
            self.debounce_timer.stop()
            self.resultados_actuales = []
            self.lista_sugerencias.clear()
            self.lista_sugerencias.hide()

    def _realizar_busqueda(self) -> None:
        texto = self.input_busqueda.text().strip()
        if len(texto) < 2:
            return

        self._search_id += 1
        current_id = self._search_id

        def _buscar():
            return self.geo_service.buscar_ciudades(texto, limite=6)

        def _on_result(ciudades: List[Ubicacion]):
            if current_id == self._search_id and self.input_busqueda.text().strip():
                self._mostrar_sugerencias(ciudades)

        ejecutar_en_segundo_plano(_buscar, on_result=_on_result)

    def _mostrar_sugerencias(self, ciudades: List[Ubicacion]) -> None:
        self.resultados_actuales = list(ciudades)
        self.lista_sugerencias.clear()

        from src.servicios.i18n import t

        if not ciudades:
            item = QListWidgetItem(t("busqueda.no_encontrado", query=self.input_busqueda.text().strip()))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista_sugerencias.addItem(item)
            self._posicionar_y_mostrar_sugerencias()
            return

        for ub in ciudades:
            region_str = f" ({ub.admin1})" if ub.admin1 and ub.admin1 != ub.ciudad else ""
            item_text = f"📍 {ub.ciudad}{region_str}, {ub.pais}"
            item = QListWidgetItem(item_text)
            self.lista_sugerencias.addItem(item)

        self.lista_sugerencias.setCurrentRow(0)
        self._posicionar_y_mostrar_sugerencias()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        idx = self.lista_sugerencias.row(item)
        if 0 <= idx < len(self.resultados_actuales):
            ub_seleccionada = self.resultados_actuales[idx]
            self.lista_sugerencias.hide()
            self.ciudad_seleccionada.emit(ub_seleccionada)
            QTimer.singleShot(25, self.limpiar)

    def _on_enter_pressed(self) -> None:
        self.debounce_timer.stop()
        row = self.lista_sugerencias.currentRow()

        if self.resultados_actuales and self.lista_sugerencias.isVisible():
            idx = row if (0 <= row < len(self.resultados_actuales)) else 0
            ub_seleccionada = self.resultados_actuales[idx]
            self.lista_sugerencias.hide()
            self.ciudad_seleccionada.emit(ub_seleccionada)
            QTimer.singleShot(25, self.limpiar)
            return

        texto = self.input_busqueda.text().strip()
        if len(texto) >= 2:
            self._search_id += 1
            current_id = self._search_id

            def _buscar_inmediato():
                return self.geo_service.buscar_ciudades(texto, limite=6)

            def _on_result_inmediato(ciudades: List[Ubicacion]):
                if current_id == self._search_id:
                    if ciudades:
                        self.lista_sugerencias.hide()
                        self.ciudad_seleccionada.emit(ciudades[0])
                        QTimer.singleShot(25, self.limpiar)
                    else:
                        self._mostrar_sugerencias([])

            ejecutar_en_segundo_plano(_buscar_inmediato, on_result=_on_result_inmediato)

    def _on_flecha_abajo(self) -> None:
        if self.lista_sugerencias.isVisible() and self.lista_sugerencias.count() > 0:
            cur = self.lista_sugerencias.currentRow()
            next_row = min(cur + 1, self.lista_sugerencias.count() - 1)
            self.lista_sugerencias.setCurrentRow(next_row)

    def _on_flecha_arriba(self) -> None:
        if self.lista_sugerencias.isVisible() and self.lista_sugerencias.count() > 0:
            cur = self.lista_sugerencias.currentRow()
            prev_row = max(cur - 1, 0)
            self.lista_sugerencias.setCurrentRow(prev_row)

    def limpiar(self) -> None:
        self.debounce_timer.stop()
        self.input_busqueda.clear()
        self.lista_sugerencias.clear()
        self.lista_sugerencias.hide()
        self.resultados_actuales = []
        self.input_busqueda.clearFocus()
