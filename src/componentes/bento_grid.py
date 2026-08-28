from typing import Optional

from PySide6.QtWidgets import QGridLayout, QWidget

from src.componentes.tarjetas_metricas import (
    TarjetaCalidadAire,
    TarjetaFaseLunar,
    TarjetaHumedad,
    TarjetaIndiceUV,
    TarjetaPresion,
    TarjetaSol,
    TarjetaViento,
    TarjetaVisibilidad,
)
from src.modelos.clima_datos import ClimaActual, PronosticoDia, PronosticoHora
from src.servicios.i18n import t
from src.utils.fecha_utils import FechaHelper
from src.utils.unidades import celsius_desde, convertir_temperatura, sufijo_temperatura, sufijo_viento


class BentoGridWidget(QWidget):
    """
    Cuadrícula modular (Bento Grid) que organiza las 8 tarjetas de métricas climáticas,
    ambientales y astronómicas (Índice UV, Viento, Fase Lunar, Sol, Calidad del Aire,
    Humedad, Visibilidad y Presión). Permite actualización en tiempo real.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(14)
        self.grid_layout.setVerticalSpacing(14)

        # Fila 0: UV y Viento
        self.card_uv = TarjetaIndiceUV(self)
        self.card_viento = TarjetaViento(self)
        self.grid_layout.addWidget(self.card_uv, 0, 0)
        self.grid_layout.addWidget(self.card_viento, 0, 1)

        # Fila 1: Fase Lunar y Sol
        self.card_luna = TarjetaFaseLunar(self)
        self.card_sol = TarjetaSol(self)
        self.grid_layout.addWidget(self.card_luna, 1, 0)
        self.grid_layout.addWidget(self.card_sol, 1, 1)

        # Fila 2: Calidad del Aire y Humedad
        self.card_calidad_aire = TarjetaCalidadAire(self)
        self.card_humedad = TarjetaHumedad(self)
        self.grid_layout.addWidget(self.card_calidad_aire, 2, 0)
        self.grid_layout.addWidget(self.card_humedad, 2, 1)

        # Fila 3: Visibilidad y Presión
        self.card_visibilidad = TarjetaVisibilidad(self)
        self.card_presion = TarjetaPresion(self)
        self.grid_layout.addWidget(self.card_visibilidad, 3, 0)
        self.grid_layout.addWidget(self.card_presion, 3, 1)

    def actualizar_datos(self, actual: ClimaActual) -> None:
        """Actualiza todas las tarjetas de métricas para el clima actual en vivo."""
        self.card_uv.actualizar(actual)
        self.card_viento.actualizar(actual)
        self.card_luna.actualizar(actual)
        self.card_sol.actualizar(actual)
        self.card_calidad_aire.actualizar(actual)
        self.card_humedad.actualizar(actual)
        self.card_visibilidad.actualizar(actual)
        self.card_presion.actualizar(actual)

    def actualizar_por_hora(self, hora: PronosticoHora, amanecer_iso: str = "", ocaso_iso: str = "") -> None:
        """Actualiza el Bento Grid para reflejar las métricas de una hora específica seleccionada."""
        # 1. UV
        self.card_uv.lbl_valor.setText(f"{hora.indice_uv:.0f}")
        if hora.indice_uv <= 2:
            cat = "Bajo"
            desc = f"Nivel seguro a las {hora.hora_etiqueta}."
        elif hora.indice_uv <= 5:
            cat = "Moderado"
            desc = f"Protección solar recomendada a las {hora.hora_etiqueta}."
        elif hora.indice_uv <= 7:
            cat = "Alto"
            desc = f"Protección solar necesaria a las {hora.hora_etiqueta}."
        else:
            cat = "Extremo"
            desc = f"Evita exposición al sol a las {hora.hora_etiqueta}."
        self.card_uv.lbl_categoria.setText(cat)
        self.card_uv.lbl_desc.setText(desc)

        # 2. Viento
        self.card_viento.lbl_velocidad.setText(f"{round(hora.viento_velocidad)} {sufijo_viento()}")
        direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                       "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        idx = int((hora.viento_direccion + 11.25) / 22.5) % 16
        cardinal = direcciones[idx]
        self.card_viento.lbl_direccion.setText(f"{cardinal} ({hora.viento_direccion}°)")
        self.card_viento.lbl_rafagas.setText(f"Pronóstico para {hora.hora_etiqueta}")
        self.card_viento.brujula.set_direccion(hora.viento_direccion)

        # 3. Sol
        if amanecer_iso and ocaso_iso:
            self.card_sol.arco.set_tiempos(amanecer_iso, ocaso_iso, hora_referencia_iso=hora.fecha_hora_iso)
            am_str = FechaHelper.formato_hora_corta(amanecer_iso)
            oc_str = FechaHelper.formato_hora_corta(ocaso_iso)
            if self.card_sol.arco.es_de_dia:
                self.card_sol.lbl_principal.setText(t("sol.ocaso_hoy", hora=oc_str))
                self.card_sol.lbl_secundario.setText(f"☀️ Posición a las {hora.hora_etiqueta}")
            else:
                self.card_sol.lbl_principal.setText(t("sol.amanecer_hoy", hora=am_str))
                self.card_sol.lbl_secundario.setText(f"🌙 Noche a las {hora.hora_etiqueta}")

        # 4. Humedad y Punto de Rocío
        self.card_humedad.lbl_valor.setText(f"{hora.humedad_relativa}%")
        rocio_c = celsius_desde(hora.temperatura) - ((100 - hora.humedad_relativa) / 5.0)
        rocio = round(convertir_temperatura(rocio_c), 1)
        self.card_humedad.lbl_punto_rocio.setText(f"Punto de rocío: {rocio}{sufijo_temperatura()} a las {hora.hora_etiqueta}.")

        # 5. Presión y Visibilidad
        self.card_presion.lbl_valor.setText(f"{hora.presion_hpa:.0f} hPa")
        self.card_visibilidad.lbl_valor.setText(f"{hora.visibilidad_km:.1f} km")

    def actualizar_por_dia(self, dia: PronosticoDia) -> None:
        """Actualiza el Bento Grid para reflejar las métricas de un día seleccionado."""
        # 1. UV Máximo
        self.card_uv.lbl_valor.setText(f"{dia.indice_uv_max:.0f}")
        if dia.indice_uv_max <= 2:
            self.card_uv.lbl_categoria.setText("Bajo")
        elif dia.indice_uv_max <= 5:
            self.card_uv.lbl_categoria.setText("Moderado")
        elif dia.indice_uv_max <= 7:
            self.card_uv.lbl_categoria.setText("Alto")
        else:
            self.card_uv.lbl_categoria.setText("Extremo")
        self.card_uv.lbl_desc.setText(f"Índice UV máximo pronosticado para {dia.nombre_dia}.")

        # 2. Sol
        if dia.amanecer_iso and dia.ocaso_iso:
            am_str = FechaHelper.formato_hora_corta(dia.amanecer_iso)
            oc_str = FechaHelper.formato_hora_corta(dia.ocaso_iso)
            self.card_sol.lbl_principal.setText(f"Ocaso: {oc_str}")
            self.card_sol.lbl_secundario.setText(f"Amanecer: {am_str}")
            self.card_sol.arco.set_tiempos(dia.amanecer_iso, dia.ocaso_iso)

        # 3. Métricas medias del día
        if dia.horas:
            hum_prom = int(sum(h.humedad_relativa for h in dia.horas) / len(dia.horas))
            viento_prom = sum(h.viento_velocidad for h in dia.horas) / len(dia.horas)
            presion_prom = sum(h.presion_hpa for h in dia.horas) / len(dia.horas)
            vis_prom = sum(h.visibilidad_km for h in dia.horas) / len(dia.horas)
            viento_dir = dia.horas[12].viento_direccion if len(dia.horas) > 12 else dia.horas[0].viento_direccion

            self.card_humedad.lbl_valor.setText(f"{hum_prom}%")
            self.card_humedad.lbl_punto_rocio.setText(f"Humedad media estimada para {dia.nombre_dia}.")

            self.card_viento.lbl_velocidad.setText(f"{round(viento_prom)} km/h")
            direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                           "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
            idx = int((viento_dir + 11.25) / 22.5) % 16
            self.card_viento.lbl_direccion.setText(f"{direcciones[idx]} ({viento_dir}°)")
            self.card_viento.lbl_rafagas.setText(f"Viento estimado para {dia.nombre_dia}")
            self.card_viento.brujula.set_direccion(viento_dir)

            self.card_presion.lbl_valor.setText(f"{presion_prom:.0f} hPa")
            self.card_visibilidad.lbl_valor.setText(f"{vis_prom:.1f} km")
