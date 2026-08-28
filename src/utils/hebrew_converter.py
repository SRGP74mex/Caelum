from typing import Tuple


class CalendarioHebreo:
    """
    Conversor astronómico y matemático para el Calendario Hebreo (Lunisolar).
    Implementa el ciclo metónico de 19 años, las reglas de aplazamiento (Dehiyyot)
    de Rosh Hashaná y el cálculo de la duración de meses variables (Cheshvan/Kislev).
    """

    MESES_NOMBRES_DEFAULT = {
        1: "Nisan",
        2: "Iyar",
        3: "Sivan",
        4: "Tammuz",
        5: "Av",
        6: "Elul",
        7: "Tishrei",
        8: "Cheshvan",
        9: "Kislev",
        10: "Tevet",
        11: "Shevat",
        12: "Adar",
        13: "Adar II",
    }

    @staticmethod
    def es_bisiesto(hebrew_year: int) -> bool:
        """Determina si un año hebreo es embolísmico (13 meses)."""
        return ((7 * hebrew_year + 1) % 19) < 7

    @staticmethod
    def meses_en_anio(hebrew_year: int) -> int:
        """Retorna 13 si el año es bisiesto, 12 si es común."""
        return 13 if CalendarioHebreo.es_bisiesto(hebrew_year) else 12

    @staticmethod
    def _dias_transcurridos(hebrew_year: int) -> int:
        """Calcula los días transcurridos desde la época hebrea hasta Rosh Hashaná del año dado."""
        m_transcurridos = (
            (235 * ((hebrew_year - 1) // 19))
            + (12 * ((hebrew_year - 1) % 19))
            + ((((hebrew_year - 1) % 19) * 7 + 1) // 19)
        )
        partes_transcurridas = 204 + 793 * (m_transcurridos % 1080)
        horas_transcurridas = 5 + 12 * m_transcurridos + 793 * (m_transcurridos // 1080) + partes_transcurridas // 1080
        partes = (partes_transcurridas % 1080) + 1080 * (horas_transcurridas % 24)
        dia = 1 + 29 * m_transcurridos + horas_transcurridas // 24

        # Reglas de Dehiyyot (Postposiciones de Rosh Hashaná)
        if (
            (partes >= 19440)
            or (
                ((dia % 7) == 2)
                and (partes >= 9924)
                and not CalendarioHebreo.es_bisiesto(hebrew_year)
            )
            or (
                ((dia % 7) == 1)
                and (partes >= 16789)
                and CalendarioHebreo.es_bisiesto(hebrew_year - 1)
            )
        ):
            alt_dia = dia + 1
        else:
            alt_dia = dia

        # No puede caer en domingo, miércoles ni viernes (Adu)
        if (alt_dia % 7) in [0, 3, 5]:
            alt_dia += 1
        return alt_dia

    @staticmethod
    def dias_en_anio(hebrew_year: int) -> int:
        """Retorna el número total de días en el año hebreo (353, 354, 355, 383, 384 o 385)."""
        return (
            CalendarioHebreo._dias_transcurridos(hebrew_year + 1)
            - CalendarioHebreo._dias_transcurridos(hebrew_year)
        )

    @staticmethod
    def es_cheshvan_largo(hebrew_year: int) -> bool:
        """Determina si Cheshvan tiene 30 días (año abundante/completo)."""
        return (CalendarioHebreo.dias_en_anio(hebrew_year) % 10) == 5

    @staticmethod
    def es_kislev_corto(hebrew_year: int) -> bool:
        """Determina si Kislev tiene 29 días (año deficiente)."""
        return (CalendarioHebreo.dias_en_anio(hebrew_year) % 10) == 3

    @staticmethod
    def dias_en_mes(month: int, hebrew_year: int) -> int:
        """Retorna la cantidad de días para un mes dado en un año hebreo específico."""
        if month in [2, 4, 6, 10]:  # Iyar, Tammuz, Elul, Tevet
            return 29
        if month == 12 and not CalendarioHebreo.es_bisiesto(hebrew_year):
            return 29
        if month == 13:  # Adar II
            return 29
        if month == 8 and not CalendarioHebreo.es_cheshvan_largo(hebrew_year):
            return 29
        if month == 9 and CalendarioHebreo.es_kislev_corto(hebrew_year):
            return 29
        return 30

    @staticmethod
    def _gregoriano_a_rd(year: int, month: int, day: int) -> int:
        """Calcula el número de Rata Die (días absolutos) para una fecha gregoriana."""
        y = year - 1
        d = 365 * y + y // 4 - y // 100 + y // 400
        dias_meses = [
            31,
            28 + (1 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 0),
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ]
        d += sum(dias_meses[: month - 1]) + day
        return d

    @staticmethod
    def _hebreo_a_rd(year: int, month: int, day: int) -> int:
        """Convierte una fecha hebrea a días Rata Die."""
        rd = CalendarioHebreo._dias_transcurridos(year) - 1373429 + day
        if month < 7:
            for m in range(7, CalendarioHebreo.meses_en_anio(year) + 1):
                rd += CalendarioHebreo.dias_en_mes(m, year)
            for m in range(1, month):
                rd += CalendarioHebreo.dias_en_mes(m, year)
        else:
            for m in range(7, month):
                rd += CalendarioHebreo.dias_en_mes(m, year)
        return rd

    @classmethod
    def de_gregoriano(cls, year: int, month: int, day: int) -> Tuple[int, int, int]:
        """
        Convierte una fecha Gregoriana (año, mes, día) a fecha Hebrea (año_h, mes_h, dia_h).
        Los meses siguen el orden eclesiástico estándar:
        1: Nisan, 2: Iyar, 3: Sivan, 4: Tammuz, 5: Av, 6: Elul,
        7: Tishrei, 8: Cheshvan, 9: Kislev, 10: Tevet, 11: Shevat,
        12: Adar (o Adar I en años bisiestos), 13: Adar II.
        """
        rd = cls._gregoriano_a_rd(year, month, day)
        h_year = (rd + 1373429) // 365
        while rd >= cls._hebreo_a_rd(h_year + 1, 7, 1):
            h_year += 1
        while rd < cls._hebreo_a_rd(h_year, 7, 1):
            h_year -= 1

        start_month = 7 if rd >= cls._hebreo_a_rd(h_year, 7, 1) else 1
        h_month = start_month
        while rd > cls._hebreo_a_rd(h_year, h_month, cls.dias_en_mes(h_month, h_year)):
            h_month += 1
            if h_month > cls.meses_en_anio(h_year):
                h_month = 1

        h_day = rd - cls._hebreo_a_rd(h_year, h_month, 1) + 1
        return h_year, h_month, h_day

