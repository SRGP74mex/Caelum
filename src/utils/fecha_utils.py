from datetime import datetime, date
from typing import Optional, Tuple
from dateutil import parser
from hijri_converter import Gregorian

DIAS_SEMANA_CORTO = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DIAS_SEMANA_COMPLETO = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_GREGORIANO = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

MESES_HIJRI_ES = [
    "Muharram", "Safar", "Rabi' al-Awwal", "Rabi' al-Thani",
    "Jumada al-Awwal", "Jumada al-Thani", "Rayab", "Sha'ban",
    "Ramadán", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"
]

class FechaHelper:
    @staticmethod
    def parse_iso(fecha_str: str) -> datetime:
        """Parsea una cadena ISO de fecha/hora de forma robusta."""
        return parser.parse(fecha_str)

    @staticmethod
    def fecha_gregoriana_legible(dt: Optional[datetime] = None) -> str:
        """Ej: 'Martes, 25 de Agosto de 2026'"""
        if dt is None:
            dt = datetime.now()
        dia_nom = DIAS_SEMANA_COMPLETO[dt.weekday()]
        mes_nom = MESES_GREGORIANO[dt.month - 1]
        return f"{dia_nom}, {dt.day} de {mes_nom} de {dt.year}"

    @staticmethod
    def fecha_hijri_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '12 Safar 1448 AH'"""
        if dt is None:
            dt = datetime.now()
        hijri = Gregorian(dt.year, dt.month, dt.day).to_hijri()
        nombre_mes = MESES_HIJRI_ES[hijri.month - 1]
        return f"{hijri.day} {nombre_mes} {hijri.year} AH"

    @staticmethod
    def fecha_dual_completa(dt: Optional[datetime] = None) -> Tuple[str, str]:
        """Retorna tupla (gregoriana, hijri)"""
        if dt is None:
            dt = datetime.now()
        return (
            FechaHelper.fecha_gregoriana_legible(dt),
            FechaHelper.fecha_hijri_legible(dt)
        )

    @staticmethod
    def nombre_dia_pronostico(fecha_iso: str, es_hoy: bool = False) -> str:
        """Retorna 'Hoy', 'Lun', 'Mar', etc."""
        if es_hoy:
            return "Hoy"
        dt = parser.parse(fecha_iso)
        return DIAS_SEMANA_CORTO[dt.weekday()]

    @staticmethod
    def formato_hora_corta(fecha_hora_iso: str) -> str:
        """Extrae '18:00' de un ISO timestamp."""
        dt = parser.parse(fecha_hora_iso)
        return dt.strftime("%H:%M")

    @staticmethod
    def diferencia_horas_solar(hora_iso: str, referencia_dt: Optional[datetime] = None) -> str:
        """Calcula el tiempo restante relativo (ej: 'en 2 horas' o 'hace 45 min')."""
        if referencia_dt is None:
            referencia_dt = datetime.now()
        dt_evento = parser.parse(hora_iso)
        if dt_evento.tzinfo:
            # Si tiene timezone, convertimos referencia_dt para evitar errores
            referencia_dt = referencia_dt.astimezone(dt_evento.tzinfo)
        diff_segundos = (dt_evento - referencia_dt).total_seconds()
        minutos = int(abs(diff_segundos) // 60)
        horas = minutos // 60
        mins_restantes = minutos % 60

        sufijo = "en" if diff_segundos >= 0 else "hace"
        if horas > 0:
            return f"{sufijo} {horas}h {mins_restantes}m"
        return f"{sufijo} {minutos}m"

