from datetime import date
from typing import Tuple


class CalendarioHebreo:
    """Conversor matemático para el Calendario Hebreo (Lunisolar)."""

    @staticmethod
    def es_bisiesto(hebrew_year: int) -> bool:
        return ((7 * hebrew_year + 1) % 19) < 7

    @staticmethod
    def meses_en_anio(hebrew_year: int) -> int:
        return 13 if CalendarioHebreo.es_bisiesto(hebrew_year) else 12

    @staticmethod
    def _dias_transcurridos(hebrew_year: int) -> int:
        m_transcurridos = (
            (235 * ((hebrew_year - 1) // 19))
            + (12 * ((hebrew_year - 1) % 19))
            + ((((hebrew_year - 1) % 19) * 7 + 1) // 19)
        )
        partes_transcurridas = 204 + 793 * (m_transcurridos % 1080)
        horas_transcurridas = 5 + 12 * m_transcurridos + 793 * (m_transcurridos // 1080) + partes_transcurridas // 1080
        partes = (partes_transcurridas % 1080) + 1080 * (horas_transcurridas % 24)
        dia = 1 + 29 * m_transcurridos + horas_transcurridas // 24

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

        if (alt_dia % 7) in [0, 3, 5]:
            alt_dia += 1
        return alt_dia

    @staticmethod
    def dias_en_anio(hebrew_year: int) -> int:
        return (
            CalendarioHebreo._dias_transcurridos(hebrew_year + 1)
            - CalendarioHebreo._dias_transcurridos(hebrew_year)
        )

    @staticmethod
    def es_cheshvan_largo(hebrew_year: int) -> bool:
        return (CalendarioHebreo.dias_en_anio(hebrew_year) % 10) == 5

    @staticmethod
    def es_kislev_corto(hebrew_year: int) -> bool:
        return (CalendarioHebreo.dias_en_anio(hebrew_year) % 10) == 3

    @staticmethod
    def dias_en_mes(month: int, hebrew_year: int) -> int:
        if month in [2, 4, 6, 10]:
            return 29
        if month == 12 and not CalendarioHebreo.es_bisiesto(hebrew_year):
            return 29
        if month == 13:
            return 29
        if month == 8 and not CalendarioHebreo.es_cheshvan_largo(hebrew_year):
            return 29
        if month == 9 and CalendarioHebreo.es_kislev_corto(hebrew_year):
            return 29
        return 30

    @staticmethod
    def _gregoriano_a_rd(year: int, month: int, day: int) -> int:
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


class CalendarioJalali:
    """Conversor para el Calendario Solar Persa / Iraní (Jalali / Solar Hijri - SH)."""

    @staticmethod
    def de_gregoriano(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        gy2 = gy + 1 if gm > 2 else gy
        days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
        jy = -1595 + (33 * (days // 12053))
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365
        if days < 186:
            jm = 1 + (days // 31)
            jd = 1 + (days % 31)
        else:
            jm = 7 + ((days - 186) // 30)
            jd = 1 + ((days - 186) % 30)
        return jy, jm, jd


class CalendarioBudista:
    """Conversor para la Era Budista (Buddhist Era - BE)."""

    @staticmethod
    def de_gregoriano(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        return gy + 543, gm, gd


class CalendarioEtiope:
    """Conversor para el Calendario Copto / Etíope (Ge'ez - EE, 13 meses)."""

    @staticmethod
    def de_gregoriano(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        y = gy
        m = gm
        if m <= 2:
            y -= 1
            m += 12
        a = y // 100
        b = 2 - a + (a // 4)
        jdn = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + gd + b - 1524

        r = (jdn - 1723856) % 1461
        n = (r % 365) + 365 * (r // 1460)
        ey = 4 * ((jdn - 1723856) // 1461) + (r // 365) - (r // 1460)
        em = (n // 30) + 1
        ed = (n % 30) + 1
        return ey, em, ed


class CalendarioSaka:
    """Conversor para el Calendario Nacional Indio (Saka Samvat)."""

    @staticmethod
    def de_gregoriano(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        is_leap = (gy % 4 == 0 and (gy % 100 != 0 or gy % 400 == 0))
        saka_year = gy - 78
        days_in_months = [0, 31, 28 + (1 if is_leap else 0), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day_of_year = sum(days_in_months[:gm]) + gd

        chaitra_start = 80 if is_leap else 81
        saka_months_lengths = [30 + (1 if is_leap else 0), 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30]

        if day_of_year >= chaitra_start:
            d = day_of_year - chaitra_start
            sm = 1
            sd = 1
            for m_len in saka_months_lengths:
                if d < m_len:
                    sd = d + 1
                    break
                d -= m_len
                sm += 1
        else:
            saka_year -= 1
            prev_is_leap = ((gy - 1) % 4 == 0 and ((gy - 1) % 100 != 0 or (gy - 1) % 400 == 0))
            prev_chaitra = 80 if prev_is_leap else 81
            days_in_prev_year = 366 if prev_is_leap else 365
            d = (days_in_prev_year - prev_chaitra) + day_of_year
            sm = 1
            sd = 1
            prev_months_lengths = [30 + (1 if prev_is_leap else 0), 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30]
            for m_len in prev_months_lengths:
                if d < m_len:
                    sd = d + 1
                    break
                d -= m_len
                sm += 1

        return saka_year, sm, sd


class CalendarioChino:
    """Conversor para el Calendario Lunisolar Chino Tradicional (Nónglì / 农历)."""

    LUNAR_INFO = [
        0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,  # 1900-1909
        0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,  # 1910-1919
        0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,  # 1920-1929
        0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,  # 1930-1939
        0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,  # 1940-1949
        0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5d0, 0x14573, 0x052d0, 0x0a9a8, 0x0e950, 0x06aa0,  # 1950-1959
        0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,  # 1960-1969
        0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b5a0, 0x195a6,  # 1970-1979
        0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,  # 1980-1989
        0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,  # 1990-1999
        0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,  # 2000-2009
        0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,  # 2010-2019
        0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,  # 2020-2029
        0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,  # 2030-2039
        0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,  # 2040-2049
        0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06aa0, 0x1a6c4, 0x0aae0,  # 2050-2059
        0x092e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,  # 2060-2069
        0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,  # 2070-2079
        0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,  # 2080-2089
        0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,  # 2090-2099
        0x0d520,                                                                                     # 2100
    ]

    ZODIACO_KEYS = ["rata", "buey", "tigre", "conejo", "dragon", "serpiente", "caballo", "cabra", "mono", "gallo", "perro", "cerdo"]

    @classmethod
    def de_gregoriano(cls, gy: int, gm: int, gd: int) -> Tuple[int, int, int, bool, str]:
        """
        Retorna (año_lunar, mes_lunar, dia_lunar, es_mes_bisiesto, clave_zodiaco).
        """
        base_date = date(1900, 1, 31)
        target_date = date(gy, gm, gd)
        offset = (target_date - base_date).days

        year = 1900
        while year <= 2100 and offset > 0:
            info = cls.LUNAR_INFO[year - 1900]
            days_in_year = 0
            for i in range(12):
                days_in_year += 30 if (info & (0x8000 >> i)) else 29
            leap_month = info & 0xF
            if leap_month > 0:
                days_in_year += 30 if (info & 0x10000) else 29

            if offset < days_in_year:
                break
            offset -= days_in_year
            year += 1

        info = cls.LUNAR_INFO[year - 1900]
        leap_month = info & 0xF
        is_leap = False

        month = 1
        for i in range(12):
            month_days = 30 if (info & (0x8000 >> (month - 1))) else 29
            if offset < month_days:
                break
            offset -= month_days

            if leap_month > 0 and month == leap_month and not is_leap:
                is_leap = True
                leap_days = 30 if (info & 0x10000) else 29
                if offset < leap_days:
                    break
                offset -= leap_days
                is_leap = False
            month += 1

        day = offset + 1
        zodiac_idx = (year - 4) % 12
        return year, month, day, is_leap, cls.ZODIACO_KEYS[zodiac_idx]

