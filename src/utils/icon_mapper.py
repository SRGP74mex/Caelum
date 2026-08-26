from src.modelos.clima_datos import CondicionClimatica

# Mapeo WMO -> (Descripción Español, Icono Día, Icono Noche, Tipo Animación)
WMO_TABLE = {
    0: ("Despejado", "clear-day", "clear-night", "clear"),
    1: ("Mayormente Despejado", "clear-day", "clear-night", "clear"),
    2: ("Parcialmente Nublado", "partly-cloudy-day", "partly-cloudy-night", "clouds"),
    3: ("Nublado", "cloudy", "cloudy", "clouds"),
    45: ("Niebla", "fog-day", "fog-night", "fog"),
    48: ("Niebla con Escarcha", "fog-day", "fog-night", "fog"),
    51: ("Llovizna Ligera", "drizzle", "drizzle", "rain"),
    53: ("Llovizna Moderada", "drizzle", "drizzle", "rain"),
    55: ("Llovizna Intensa", "drizzle", "drizzle", "rain"),
    56: ("Llovizna Helada Ligera", "sleet", "sleet", "snow"),
    57: ("Llovizna Helada Densa", "sleet", "sleet", "snow"),
    61: ("Lluvia Ligera", "partly-cloudy-day-rain", "partly-cloudy-night-rain", "rain"),
    63: ("Lluvia Moderada", "rain", "rain", "rain"),
    65: ("Lluvia Fuerte", "heavy-rain", "heavy-rain", "rain"),
    66: ("Lluvia Helada Ligera", "sleet", "sleet", "snow"),
    67: ("Lluvia Helada Fuerte", "sleet", "sleet", "snow"),
    71: ("Nieve Ligera", "partly-cloudy-day-snow", "partly-cloudy-night-snow", "snow"),
    73: ("Nieve Moderada", "snow", "snow", "snow"),
    75: ("Nieve Fuerte", "heavy-snow", "heavy-snow", "snow"),
    77: ("Granos de Nieve", "snowflake", "snowflake", "snow"),
    80: ("Chubascos Leves", "partly-cloudy-day-rain", "partly-cloudy-night-rain", "rain"),
    81: ("Chubascos Moderados", "rain", "rain", "rain"),
    82: ("Chubascos Violentos", "heavy-rain", "heavy-rain", "rain"),
    85: ("Chubascos de Nieve Leves", "partly-cloudy-day-snow", "partly-cloudy-night-snow", "snow"),
    86: ("Chubascos de Nieve Fuertes", "heavy-snow", "heavy-snow", "snow"),
    95: ("Tormenta Eléctrica", "thunderstorms-day", "thunderstorms-night", "thunderstorm"),
    96: ("Tormenta con Granizo Leve", "thunderstorms-day-rain", "thunderstorms-night-rain", "thunderstorm"),
    99: ("Tormenta con Granizo Fuerte", "thunderstorms-day-rain", "thunderstorms-night-rain", "thunderstorm"),
}

class IconMapper:
    @staticmethod
    def obtener_condicion(wmo_code: int, es_dia: bool = True) -> CondicionClimatica:
        info = WMO_TABLE.get(wmo_code, ("Variable", "cloudy", "cloudy", "clouds"))
        descripcion, icon_dia, icon_noche, animacion = info
        icon_name = icon_dia if es_dia else icon_noche
        return CondicionClimatica(
            wmo_code=wmo_code,
            descripcion=descripcion,
            icon_name=icon_name,
            es_dia=es_dia,
            animacion_tipo=animacion
        )

    @staticmethod
    def mapear_owm_a_wmo(owm_icon: str, owm_id: int) -> int:
        """Convierte códigos de OpenWeatherMap a códigos estándar WMO si se usa OWM."""
        if 200 <= owm_id < 300:
            return 95 # Tormenta
        elif 300 <= owm_id < 400:
            return 51 # Llovizna
        elif 500 <= owm_id < 510:
            return 61 if owm_id == 500 else 63 # Lluvia
        elif owm_id == 511:
            return 66 # Lluvia helada
        elif 520 <= owm_id < 600:
            return 80 # Chubascos
        elif 600 <= owm_id < 700:
            return 71 # Nieve
        elif 700 <= owm_id < 800:
            return 45 # Niebla
        elif owm_id == 800:
            return 0 # Despejado
        elif owm_id == 801:
            return 1
        elif owm_id == 802:
            return 2
        elif owm_id >= 803:
            return 3
        return 0

