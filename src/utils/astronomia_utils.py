import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class InfoLuna:
    nombre: str
    archivo_icono: str
    iluminacion_pct: int
    edad_dias: float
    proxima_luna_llena: str  # Formato legible ej: "14 Sep"
    salida_estimada: str     # ej: "20:15"
    puesta_estimada: str     # ej: "07:30"


class AstronomiaHelper:
    """
    Utilidades astronómicas para cálculo preciso del ciclo sinódico lunar (29.53 días),
    porcentaje de iluminación, fase actual e hitos de plenilunio.
    """
    DURACION_MES_SINODICO = 29.53058867
    # Referencia astronómica conocida (Luna nueva: 6 de enero de 2000, 18:14 UTC)
    FECHA_BASE_LUNA_NUEVA = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

    @classmethod
    def obtener_info_lunar(
        cls,
        fecha: Optional[datetime] = None,
        amanecer_iso: Optional[str] = None,
        ocaso_iso: Optional[str] = None
    ) -> InfoLuna:
        if fecha is None:
            fecha = datetime.now(timezone.utc)
        elif fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)

        diff_segundos = (fecha - cls.FECHA_BASE_LUNA_NUEVA).total_seconds()
        diff_dias = diff_segundos / 86400.0
        ciclo = diff_dias % cls.DURACION_MES_SINODICO
        fase_frac = ciclo / cls.DURACION_MES_SINODICO  # 0.0 a 1.0

        # Iluminación geométrica proporcional: (1 - cos(2*pi*fase)) / 2 * 100
        iluminacion = round((1.0 - math.cos(2.0 * math.pi * fase_frac)) / 2.0 * 100)

        from src.servicios.i18n import t

        # Mapeo a las 8 fases estándar
        if fase_frac < 0.035 or fase_frac >= 0.965:
            nombre = t("luna.nueva")
            archivo = "luna_nueva.png"
        elif fase_frac < 0.215:
            nombre = t("luna.creciente_fertil")
            archivo = "luna_creciente_concava.png"
        elif fase_frac < 0.285:
            nombre = t("luna.cuarto_creciente")
            archivo = "luna_cuarto_creciente.png"
        elif fase_frac < 0.465:
            nombre = t("luna.gibosa_creciente")
            archivo = "luna_creciente_gibosa.png"
        elif fase_frac < 0.535:
            nombre = t("luna.llena")
            archivo = "luna_llena.png"
        elif fase_frac < 0.715:
            nombre = t("luna.gibosa_menguante")
            archivo = "luna_menguante_gibosa.png"
        elif fase_frac < 0.785:
            nombre = t("luna.cuarto_menguante")
            archivo = "luna_cuarto_menguante.png"
        else:
            nombre = t("luna.menguante")
            archivo = "luna_menguante_concava.png"

        # Próxima Luna Llena (fase_frac = 0.5)
        dias_para_llena = (0.5 - fase_frac) * cls.DURACION_MES_SINODICO
        if dias_para_llena <= 0:
            dias_para_llena += cls.DURACION_MES_SINODICO
        fecha_llena = fecha + timedelta(days=dias_para_llena)
        mes_str = t(f"meses.{fecha_llena.month}")
        str_llena = f"{fecha_llena.day} {mes_str}"

        # Estimación de Salida / Puesta de la Luna basada en el desfase sinódico
        hora_salida_base = 6.0
        hora_puesta_base = 18.0

        if amanecer_iso and "T" in amanecer_iso:
            try:
                hora_part = amanecer_iso.split("T")[1][:5]
                hh, mm = map(int, hora_part.split(":"))
                hora_salida_base = hh + mm / 60.0
            except Exception:
                pass

        if ocaso_iso and "T" in ocaso_iso:
            try:
                hora_part = ocaso_iso.split("T")[1][:5]
                hh, mm = map(int, hora_part.split(":"))
                hora_puesta_base = hh + mm / 60.0
            except Exception:
                pass

        desfase_horas = (fase_frac * 24.0) % 24.0
        salida_luna_h = (hora_salida_base + desfase_horas) % 24.0
        puesta_luna_h = (hora_puesta_base + desfase_horas) % 24.0

        sh_int = int(salida_luna_h)
        sm_int = int((salida_luna_h - sh_int) * 60.0)
        str_salida = f"{sh_int:02d}:{sm_int:02d}"

        ph_int = int(puesta_luna_h)
        pm_int = int((puesta_luna_h - ph_int) * 60.0)
        str_puesta = f"{ph_int:02d}:{pm_int:02d}"

        return InfoLuna(
            nombre=nombre,
            archivo_icono=archivo,
            iluminacion_pct=iluminacion,
            edad_dias=round(ciclo, 1),
            proxima_luna_llena=str_llena,
            salida_estimada=str_salida,
            puesta_estimada=str_puesta
        )

