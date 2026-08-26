"""Conversión de unidades para las preferencias de usuario (temperatura/viento).

El estado de la unidad activa se guarda a nivel de módulo (como ya hace
config.LANGUAGE) porque los widgets de src/componentes/ construyen sus
etiquetas de texto sin recibir las preferencias como parámetro; así evitamos
tener que enhebrar `prefs` a través de cada método `actualizar()`/`set_datos()`
de los 9 componentes. Es aceptable en una app de escritorio de un solo hilo
de UI, sin estado concurrente que proteger.
"""
from dataclasses import replace
from typing import Dict, Optional

from src.modelos.clima_datos import PronosticoDia, PronosticoHora, ReporteClimaCompleto

_estado_unidades: Dict[str, str] = {"temperatura": "celsius", "viento": "kmh"}


def establecer_preferencias_unidades(prefs: Dict[str, str]) -> None:
    """Actualiza la unidad activa a partir de las preferencias guardadas en ConfigManager."""
    if "temperatura" in prefs:
        _estado_unidades["temperatura"] = prefs["temperatura"]
    if "viento" in prefs:
        _estado_unidades["viento"] = prefs["viento"]


def sufijo_temperatura() -> str:
    return "°F" if _estado_unidades["temperatura"] == "fahrenheit" else "°C"


def sufijo_viento() -> str:
    return {"ms": "m/s", "mph": "mph"}.get(_estado_unidades["viento"], "km/h")


def convertir_temperatura(valor_c: float, unidad: Optional[str] = None) -> float:
    unidad = unidad or _estado_unidades["temperatura"]
    if unidad == "fahrenheit":
        return valor_c * 9 / 5 + 32
    return valor_c


def celsius_desde(valor: float, unidad: Optional[str] = None) -> float:
    """Inversa de convertir_temperatura: recupera el valor en Celsius desde la unidad
    activa. Necesario para fórmulas (p. ej. punto de rocío) que solo son válidas en
    Celsius y que se aplican sobre un valor ya convertido para mostrarse en pantalla."""
    unidad = unidad or _estado_unidades["temperatura"]
    if unidad == "fahrenheit":
        return (valor - 32) * 5 / 9
    return valor


def convertir_viento(valor_kmh: float, unidad: Optional[str] = None) -> float:
    unidad = unidad or _estado_unidades["viento"]
    if unidad == "ms":
        return valor_kmh / 3.6
    if unidad == "mph":
        return valor_kmh / 1.60934
    return valor_kmh


def _convertir_hora(hora: PronosticoHora) -> PronosticoHora:
    return replace(
        hora,
        temperatura=convertir_temperatura(hora.temperatura),
        sensacion=convertir_temperatura(hora.sensacion),
        viento_velocidad=convertir_viento(hora.viento_velocidad),
    )


def _convertir_dia(dia: PronosticoDia) -> PronosticoDia:
    return replace(
        dia,
        temp_min=convertir_temperatura(dia.temp_min),
        temp_max=convertir_temperatura(dia.temp_max),
        horas=[_convertir_hora(h) for h in dia.horas],
    )


def aplicar_preferencias_unidades(reporte: ReporteClimaCompleto) -> ReporteClimaCompleto:
    """Devuelve una copia del reporte con los valores numéricos convertidos a la unidad
    activa. El reporte original nunca se muta (así el caché en disco, que se guarda
    antes de llamar a esta función, siempre queda en unidades base)."""
    if _estado_unidades["temperatura"] == "celsius" and _estado_unidades["viento"] == "kmh":
        return reporte

    actual = reporte.actual
    actual_conv = replace(
        actual,
        temperatura=convertir_temperatura(actual.temperatura),
        sensacion_termica=convertir_temperatura(actual.sensacion_termica),
        temp_max_hoy=convertir_temperatura(actual.temp_max_hoy),
        temp_min_hoy=convertir_temperatura(actual.temp_min_hoy),
        punto_rocio=convertir_temperatura(actual.punto_rocio) if actual.punto_rocio is not None else None,
        viento_velocidad=convertir_viento(actual.viento_velocidad),
        viento_rafagas=convertir_viento(actual.viento_rafagas) if actual.viento_rafagas is not None else None,
    )

    return replace(
        reporte,
        actual=actual_conv,
        horas_24h=[_convertir_hora(h) for h in reporte.horas_24h],
        dias_7d=[_convertir_dia(d) for d in reporte.dias_7d],
    )
