from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Ubicacion:
    ciudad: str
    pais: str
    latitud: float
    longitud: float
    timezone: str = "auto"
    elevacion: Optional[float] = None
    admin1: Optional[str] = None  # Estado/Departamento/Provincia

@dataclass
class CondicionClimatica:
    wmo_code: int
    descripcion: str
    icon_name: str
    es_dia: bool = True
    animacion_tipo: str = "clear"  # "clear", "clouds", "rain", "snow", "thunderstorm", "fog"


@dataclass
class DatosCalidadAire:
    aqi_europeo: int               # 0-100+
    aqi_us: int                    # 0-500
    pm2_5: float                   # μg/m³
    pm10: float                    # μg/m³
    dioxido_nitrogeno: Optional[float] = None
    ozono: Optional[float] = None
    dioxido_azufre: Optional[float] = None

    @property
    def categoria(self) -> str:
        if self.aqi_us <= 50:
            return "Excelente"
        elif self.aqi_us <= 100:
            return "Aceptable"
        elif self.aqi_us <= 150:
            return "Sensible"
        elif self.aqi_us <= 200:
            return "Dañina"
        elif self.aqi_us <= 300:
            return "Muy Dañina"
        return "Peligrosa"

    @property
    def color_hex(self) -> str:
        if self.aqi_us <= 50:
            return "#34d399"  # Verde
        elif self.aqi_us <= 100:
            return "#fbbf24"  # Amarillo
        elif self.aqi_us <= 150:
            return "#fb923c"  # Naranja
        elif self.aqi_us <= 200:
            return "#f87171"  # Rojo
        elif self.aqi_us <= 300:
            return "#c084fc"  # Morado
        return "#b91c1c"      # Granate


@dataclass
class ClimaActual:
    temperatura: float
    sensacion_termica: float
    temp_max_hoy: float
    temp_min_hoy: float
    humedad_relativa: int          # %
    punto_rocio: Optional[float]   # °C
    viento_velocidad: float        # km/h
    viento_direccion: int          # Grados 0-360
    viento_rafagas: Optional[float] # km/h
    indice_uv: float               # 0-12+
    presion_hpa: float             # hPa / mbar
    visibilidad_km: float          # km
    probabilidad_lluvia: int       # %
    precipitacion_mm: float        # mm
    amanecer_iso: str              # ISO datetime
    ocaso_iso: str                 # ISO datetime
    condicion: CondicionClimatica
    calidad_aire: Optional[DatosCalidadAire] = None
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def uv_categoria(self) -> str:
        if self.indice_uv <= 2:
            return "Bajo"
        elif self.indice_uv <= 5:
            return "Moderado"
        elif self.indice_uv <= 7:
            return "Alto"
        elif self.indice_uv <= 10:
            return "Muy Alto"
        return "Extremo"

    @property
    def viento_direccion_cardinal(self) -> str:
        direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                       "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        idx = int((self.viento_direccion + 11.25) / 22.5) % 16
        return direcciones[idx]


@dataclass
class PronosticoHora:
    fecha_hora_iso: str
    hora_etiqueta: str             # "Ahora", "18:00", "19:00"
    temperatura: float
    sensacion: float
    probabilidad_lluvia: int       # %
    precipitacion_mm: float
    condicion: CondicionClimatica
    indice_uv: float = 0.0
    es_noche: bool = False
    humedad_relativa: int = 50
    viento_velocidad: float = 0.0
    viento_direccion: int = 0
    presion_hpa: float = 1013.25
    visibilidad_km: float = 10.0

@dataclass
class PronosticoDia:
    fecha_iso: str                 # YYYY-MM-DD
    nombre_dia: str                # "Hoy", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"
    temp_min: float
    temp_max: float
    probabilidad_lluvia: int
    precipitacion_total_mm: float
    amanecer_iso: str
    ocaso_iso: str
    indice_uv_max: float
    condicion: CondicionClimatica
    horas: List[PronosticoHora] = field(default_factory=list)

@dataclass
class ReporteClimaCompleto:
    ubicacion: Ubicacion
    actual: ClimaActual
    horas_24h: List[PronosticoHora]
    dias_7d: List[PronosticoDia]
    fuente: str = "Open-Meteo"
    fecha_actualizacion_iso: str = field(default_factory=lambda: datetime.now().isoformat())

