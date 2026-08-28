from datetime import datetime
from typing import Dict, List, Optional, Tuple

from dateutil import parser
from hijri_converter import Gregorian

from src.utils.calendarios_mundo import (
    CalendarioBudista,
    CalendarioChino,
    CalendarioEtiope,
    CalendarioHebreo,
    CalendarioJalali,
    CalendarioSaka,
)

DIAS_KEYS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]


class FechaHelper:
    @staticmethod
    def parse_iso(fecha_str: str) -> datetime:
        """Parsea una cadena ISO de fecha/hora de forma robusta."""
        return parser.parse(fecha_str)

    @staticmethod
    def fecha_gregoriana_legible(dt: Optional[datetime] = None) -> str:
        """Formatea fecha gregoriana adaptada al idioma activo (es, en, fr, it, de, ja)."""
        from src.servicios.i18n import obtener_idioma_actual, t

        if dt is None:
            dt = datetime.now()
        dia_key = DIAS_KEYS[dt.weekday()]
        dia_nom = t(f"dias.{dia_key}")
        mes_nom = t(f"meses.{dt.month}")
        lang = obtener_idioma_actual()

        if lang == "ja":
            return f"{dt.year}年{dt.month}月{dt.day}日 ({dia_nom})"
        elif lang in ["en", "de"]:
            return f"{dia_nom}, {mes_nom} {dt.day}, {dt.year}"
        elif lang in ["fr", "it"]:
            return f"{dia_nom} {dt.day} {mes_nom} {dt.year}"
        return f"{dia_nom}, {dt.day} de {mes_nom} de {dt.year}"

    @staticmethod
    def fecha_hijri_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '12 Safar 1448 AH' con nombres de mes traducidos."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        hijri = Gregorian(dt.year, dt.month, dt.day).to_hijri()
        nombre_mes = t(f"hijri.{hijri.month}")
        sufijo = t("hijri.sufijo")
        return f"{hijri.day} {nombre_mes} {hijri.year} {sufijo}"

    @staticmethod
    def fecha_hebrea_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '14 Elul 5786 AM' con nombres de mes traducidos y sufijo de era."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        h_year, h_month, h_day = CalendarioHebreo.de_gregoriano(dt.year, dt.month, dt.day)
        nombre_mes = t(f"hebreo.{h_month}")
        sufijo = t("hebreo.sufijo")
        return f"{h_day} {nombre_mes} {h_year} {sufijo}"

    @staticmethod
    def fecha_jalali_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '5 Shahrivar 1405 SH' (Solar Persa)."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        jy, jm, jd = CalendarioJalali.de_gregoriano(dt.year, dt.month, dt.day)
        nombre_mes = t(f"jalali.{jm}")
        sufijo = t("jalali.sufijo")
        return f"{jd} {nombre_mes} {jy} {sufijo}"

    @staticmethod
    def fecha_budista_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '27 August 2569 BE' (Era Budista)."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        by, bm, bd = CalendarioBudista.de_gregoriano(dt.year, dt.month, dt.day)
        mes_nom = t(f"meses.{bm}")
        sufijo = t("budista.sufijo")
        return f"{bd} {mes_nom} {by} {sufijo}"

    @staticmethod
    def fecha_etiope_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '21 Nehase 2018 EE' (Copto / Ge'ez)."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        ey, em, ed = CalendarioEtiope.de_gregoriano(dt.year, dt.month, dt.day)
        nombre_mes = t(f"etiope.{em}")
        sufijo = t("etiope.sufijo")
        return f"{ed} {nombre_mes} {ey} {sufijo}"

    @staticmethod
    def fecha_saka_legible(dt: Optional[datetime] = None) -> str:
        """Ej: '5 Bhadra 1948 Saka' (Nacional Indio)."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        sy, sm, sd = CalendarioSaka.de_gregoriano(dt.year, dt.month, dt.day)
        nombre_mes = t(f"saka.{sm}")
        sufijo = t("saka.sufijo")
        return f"{sd} {nombre_mes} {sy} {sufijo}"

    @staticmethod
    def fecha_china_legible(dt: Optional[datetime] = None) -> str:
        """Ej: 'Día 15 Mes 7 • Año del Caballo' (Lunisolar Chino)."""
        from src.servicios.i18n import t

        if dt is None:
            dt = datetime.now()
        cy, cm, cd, is_leap, zod_key = CalendarioChino.de_gregoriano(dt.year, dt.month, dt.day)
        bisiesto_str = f" ({t('chino.bisiesto')})" if is_leap else ""
        zod_nombre = t(f"chino.zodiaco.{zod_key}")
        return f"{t('chino.dia')} {cd} {t('chino.mes')} {cm}{bisiesto_str} • {t('chino.anio')} {zod_nombre}"

    @staticmethod
    def fecha_dual_completa(dt: Optional[datetime] = None) -> Tuple[str, str]:
        """Retorna tupla (gregoriana, hijri) para compatibilidad."""
        if dt is None:
            dt = datetime.now()
        return (
            FechaHelper.fecha_gregoriana_legible(dt),
            FechaHelper.fecha_hijri_legible(dt),
        )

    @staticmethod
    def fechas_calendarios_completas(dt: Optional[datetime] = None) -> Tuple[str, str, str]:
        """Retorna tupla (gregoriana, hijri, hebrea) para compatibilidad."""
        if dt is None:
            dt = datetime.now()
        return (
            FechaHelper.fecha_gregoriana_legible(dt),
            FechaHelper.fecha_hijri_legible(dt),
            FechaHelper.fecha_hebrea_legible(dt),
        )

    @staticmethod
    def obtener_pildoras_calendarios(
        dt: Optional[datetime] = None,
        config_calendarios: Optional[Dict[str, bool]] = None,
    ) -> List[Tuple[str, str, str]]:
        """
        Retorna una lista de tuplas (id_calendario, icono, texto_formateado)
        para todos los calendarios habilitados en la configuración.
        """
        if dt is None:
            dt = datetime.now()

        # Configuración por defecto: Gregoriano, Hijri y Hebreo activos
        cfg = {
            "gregoriano": True,
            "hijri": True,
            "hebreo": True,
            "jalali": False,
            "budista": False,
            "etiope": False,
            "saka": False,
            "chino": False,
        }
        if config_calendarios:
            cfg.update(config_calendarios)

        pildoras = []

        if cfg.get("gregoriano", True):
            pildoras.append(("gregoriano", "📅", FechaHelper.fecha_gregoriana_legible(dt)))

        if cfg.get("hijri", True):
            pildoras.append(("hijri", "🌙", FechaHelper.fecha_hijri_legible(dt)))

        if cfg.get("hebreo", True):
            pildoras.append(("hebreo", "🕎", FechaHelper.fecha_hebrea_legible(dt)))

        if cfg.get("jalali", False):
            pildoras.append(("jalali", "☀️", FechaHelper.fecha_jalali_legible(dt)))

        if cfg.get("budista", False):
            pildoras.append(("budista", "☸️", FechaHelper.fecha_budista_legible(dt)))

        if cfg.get("etiope", False):
            pildoras.append(("etiope", "🇪🇹", FechaHelper.fecha_etiope_legible(dt)))

        if cfg.get("saka", False):
            pildoras.append(("saka", "🇮🇳", FechaHelper.fecha_saka_legible(dt)))

        if cfg.get("chino", False):
            pildoras.append(("chino", "🐉", FechaHelper.fecha_china_legible(dt)))

        # Garantizar que al menos el gregoriano se muestre si todos están desactivados
        if not pildoras:
            pildoras.append(("gregoriano", "📅", FechaHelper.fecha_gregoriana_legible(dt)))

        return pildoras

    @staticmethod
    def nombre_dia_pronostico(fecha_iso: str, es_hoy: bool = False) -> str:
        """Retorna 'Hoy' / 'Today', 'Lun' / 'Mon', etc."""
        from src.servicios.i18n import t

        if es_hoy:
            return t("dias_cortos.hoy")
        dt = parser.parse(fecha_iso)
        dia_key = DIAS_KEYS[dt.weekday()]
        res = t(f"dias_cortos.{dia_key}")
        if res == dia_key:
            res = t(f"dias.{dia_key}")[:3]
        return res

    @staticmethod
    def formato_hora_corta(fecha_hora_iso: str) -> str:
        """Extrae '18:00' de un ISO timestamp."""
        dt = parser.parse(fecha_hora_iso)
        return dt.strftime("%H:%M")

    @staticmethod
    def diferencia_horas_solar(hora_iso: str, referencia_dt: Optional[datetime] = None) -> str:
        """Calcula el tiempo restante relativo."""
        if referencia_dt is None:
            referencia_dt = datetime.now()
        dt_evento = parser.parse(hora_iso)
        if dt_evento.tzinfo:
            referencia_dt = referencia_dt.astimezone(dt_evento.tzinfo)
        diff_segundos = (dt_evento - referencia_dt).total_seconds()
        minutos = int(abs(diff_segundos) // 60)
        horas = minutos // 60
        mins_restantes = minutos % 60

        sufijo = "en" if diff_segundos >= 0 else "hace"
        if horas > 0:
            return f"{sufijo} {horas}h {mins_restantes}m"
        return f"{sufijo} {minutos}m"
