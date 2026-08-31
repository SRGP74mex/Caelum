import os
import sys
from pathlib import Path

# Rutas Base del Proyecto (compatible con desarrollo, cx_Freeze y PyInstaller)
if getattr(sys, "frozen", False):
    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = Path(sys._MEIPASS).resolve()
    else:
        BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons" / "meteocons"
LUNA_DIR = ASSETS_DIR / "icons" / "luna"
STYLES_DIR = ASSETS_DIR / "styles"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
LOCALES_DIR = ASSETS_DIR / "locales"


def directorio_datos_usuario(tipo: str) -> Path:
    """Resuelve el directorio de datos de usuario ("cache" o "config") según
    la convención nativa de cada sistema operativo. El nombre de carpeta
    "weather_linux" se conserva por compatibilidad con instalaciones previas.
    """
    home = Path.home()
    nombre_carpeta = "weather_linux"

    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / nombre_carpeta / tipo.capitalize()

    if sys.platform == "darwin":
        subcarpeta = "Caches" if tipo == "cache" else "Application Support"
        return home / "Library" / subcarpeta / nombre_carpeta

    # Linux y otros Unix: convención XDG Base Directory
    variable_xdg = "XDG_CACHE_HOME" if tipo == "cache" else "XDG_CONFIG_HOME"
    carpeta_por_defecto = ".cache" if tipo == "cache" else ".config"
    base_xdg = os.environ.get(variable_xdg)
    base = Path(base_xdg) if base_xdg else home / carpeta_por_defecto
    return base / nombre_carpeta


CACHE_DIR = directorio_datos_usuario("cache")

# Crear directorio de caché si no existe
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

# Configuración de Aplicación
APP_NAME = "Caelum"
APP_ID = "caelum"

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

# Idiomas soportados
IDIOMAS_SOPORTADOS = {
    "auto": "Automático (Sistema)",
    "es": "Español",
    "en": "English",
    "fr": "Français",
    "it": "Italiano",
    "de": "Deutsch",
    "ja": "日本語"
}
DEFAULT_LANGUAGE = "auto"
LANGUAGE = "es"

# Configuración de Red y Caché
REQUEST_TIMEOUT = 10               # segundos
CACHE_TTL_SECONDS = 900            # 15 minutos de caché
GEOLOCATION_IP_API = "https://ipapi.co/json/"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
