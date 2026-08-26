from pathlib import Path

# Rutas Base del Proyecto
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons" / "meteocons"
STYLES_DIR = ASSETS_DIR / "styles"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
CACHE_DIR = Path.home() / ".cache" / "weather_linux"

# Crear directorio de caché si no existe
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

# Configuración de Aplicación
APP_NAME = "WeatherApp Linux"
APP_VERSION = "1.3.0"
APP_ID = "com.weatherlinux.app"

# Configuración de Clima por Defecto
DEFAULT_CITY = "Bogotá"
DEFAULT_LATITUDE = 4.6097
DEFAULT_LONGITUDE = -74.0817
DEFAULT_TIMEZONE = "auto"

# Unidades y Formatos
UNITS = {
    "temperature": "celsius",      # "celsius" | "fahrenheit"
    "wind_speed": "kmh",           # "kmh" | "ms" | "mph"
    "precipitation": "mm",         # "mm" | "inch"
    "pressure": "hPa"
}

LANGUAGE = "es"

# Configuración de Red y Caché
REQUEST_TIMEOUT = 10               # segundos
CACHE_TTL_SECONDS = 900            # 15 minutos de caché
GEOLOCATION_IP_API = "https://ipapi.co/json/"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

