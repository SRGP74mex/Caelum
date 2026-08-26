import logging
import re
from typing import List

from config import (
    DEFAULT_CITY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEZONE,
    LANGUAGE,
    OPEN_METEO_GEOCODING_URL,
    REQUEST_TIMEOUT,
)
from src.modelos.clima_datos import Ubicacion
from src.servicios.http_session import sesion_http

logger = logging.getLogger(__name__)

# Alias populares de ciudades y abreviaturas
ALIAS_CIUDADES = {
    "cdmx": "Ciudad de México",
    "df": "Ciudad de México",
    "edomex": "Estado de México",
    "gdl": "Guadalajara",
    "mty": "Monterrey",
    "pue": "Puebla",
    "nyc": "New York",
    "la": "Los Angeles",
    "sf": "San Francisco",
    "bcn": "Barcelona",
    "mad": "Madrid",
    "bog": "Bogotá",
    "med": "Medellín",
    "bsas": "Buenos Aires",
    "scl": "Santiago de Chile",
    "lim": "Lima",
    "sp": "São Paulo",
    "rio": "Rio de Janeiro"
}

class GeocodingService:
    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout

    def _normalizar_texto(self, consulta: str) -> str:
        """Reemplaza acrónimos y limpia separadores."""
        texto = consulta.strip()
        tokens = re.split(r'[,;\-\s]+', texto)
        tokens_normalizados = [ALIAS_CIUDADES.get(t.lower(), t) for t in tokens if t]
        return " ".join(tokens_normalizados)

    def buscar_ciudades(self, consulta: str, limite: int = 6, idioma: str = LANGUAGE) -> List[Ubicacion]:
        """
        Búsqueda inteligente multi-estrategia:
        1. Open-Meteo Geocoding con consulta procesada.
        2. Búsqueda por término principal si contiene provincia/estado.
        3. Fallback a Nominatim OpenStreetMap para búsquedas complejas.
        """
        if not consulta or len(consulta.strip()) < 2:
            return []

        query_limpia = consulta.strip()
        query_normalizada = self._normalizar_texto(query_limpia)

        # 1. Intentar Open-Meteo Geocoding directo
        resultados = self._buscar_open_meteo(query_normalizada, limite, idioma)
        if resultados:
            return resultados

        if query_normalizada != query_limpia:
            resultados = self._buscar_open_meteo(query_limpia, limite, idioma)
            if resultados:
                return resultados

        # 2. Si la consulta tiene múltiples palabras o comas
        partes = [p.strip() for p in re.split(r'[,]+', query_limpia) if p.strip()]
        if len(partes) > 1:
            resultados_partes = self._buscar_open_meteo(partes[0], limite, idioma)
            if resultados_partes:
                return resultados_partes

        # Probar con las primeras 2 palabras
        palabras = query_limpia.split()
        if len(palabras) > 2:
            sub_query = " ".join(palabras[:2])
            resultados_sub = self._buscar_open_meteo(sub_query, limite, idioma)
            if resultados_sub:
                return resultados_sub

        # 3. Fallback a Nominatim OpenStreetMap
        return self._buscar_nominatim(query_normalizada or query_limpia, limite)

    def _buscar_open_meteo(self, nombre: str, limite: int, idioma: str) -> List[Ubicacion]:
        params = {
            "name": nombre,
            "count": limite,
            "language": idioma,
            "format": "json"
        }
        try:
            response = sesion_http.get(OPEN_METEO_GEOCODING_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            resultados: List[Ubicacion] = []
            for item in data.get("results", []):
                ciudad = item.get("name", "")
                pais = item.get("country", "")
                admin1 = item.get("admin1")
                lat = float(item.get("latitude", 0.0))
                lon = float(item.get("longitude", 0.0))
                tz = item.get("timezone", "auto")
                elev = item.get("elevation")

                resultados.append(Ubicacion(
                    ciudad=ciudad,
                    pais=pais,
                    latitud=lat,
                    longitud=lon,
                    timezone=tz,
                    elevacion=float(elev) if elev is not None else None,
                    admin1=admin1
                ))
            return resultados
        except Exception:
            logger.warning("Fallo en búsqueda Open-Meteo para %r", nombre, exc_info=True)
            return []

    def _buscar_nominatim(self, query: str, limite: int) -> List[Ubicacion]:
        """Fallback usando el geocodificador Nominatim (OpenStreetMap)."""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": limite,
            "addressdetails": 1,
            "accept-language": LANGUAGE
        }
        headers = {"User-Agent": "WeatherApp-Linux/1.0 (https://github.com/weatherapp-linux)"}

        try:
            response = sesion_http.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            items = response.json()

            resultados: List[Ubicacion] = []
            for item in items:
                address = item.get("address", {})
                nombre_directo = item.get("name", "")
                suburb = address.get("neighbourhood") or address.get("suburb") or address.get("quarter") or address.get("village")
                city = address.get("city") or address.get("town") or address.get("municipality") or address.get("borough") or address.get("county")

                ciudad = suburb or nombre_directo or city or "Ubicación"
                pais = address.get("country", "")
                admin1 = address.get("borough") or address.get("state") or address.get("province") or city
                lat = float(item.get("lat", 0.0))
                lon = float(item.get("lon", 0.0))

                resultados.append(Ubicacion(
                    ciudad=ciudad,
                    pais=pais,
                    latitud=lat,
                    longitud=lon,
                    timezone="auto",
                    admin1=admin1 if admin1 != ciudad else None
                ))
            return resultados
        except Exception:
            logger.warning("Fallo en búsqueda Nominatim para %r", query, exc_info=True)
            return []

    def obtener_ciudades_cercanas(self, lat: float, lon: float, limite: int = 6) -> List[Ubicacion]:
        """Obtiene ciudades/municipios cercanos a las coordenadas detectadas por GeoIP."""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": "municipio",
            "format": "json",
            "viewbox": f"{lon-0.8},{lat+0.8},{lon+0.8},{lat-0.8}",
            "bounded": 1,
            "limit": limite,
            "addressdetails": 1,
            "accept-language": LANGUAGE
        }
        headers = {"User-Agent": "WeatherApp-Linux/1.0 (https://github.com/weatherapp-linux)"}

        try:
            response = sesion_http.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            items = response.json()

            resultados: List[Ubicacion] = []
            vistos = set()
            for item in items:
                address = item.get("address", {})
                nombre = item.get("name", "")
                city = address.get("city") or address.get("town") or address.get("municipality") or address.get("borough")
                ciudad = nombre or city or "Localidad"

                if ciudad in vistos:
                    continue
                vistos.add(ciudad)

                pais = address.get("country", "")
                admin1 = address.get("state") or address.get("province") or address.get("borough")
                lat_val = float(item.get("lat", 0.0))
                lon_val = float(item.get("lon", 0.0))

                resultados.append(Ubicacion(
                    ciudad=ciudad,
                    pais=pais,
                    latitud=lat_val,
                    longitud=lon_val,
                    timezone="auto",
                    admin1=admin1 if admin1 != ciudad else None
                ))
            return resultados
        except Exception:
            logger.warning("Fallo al obtener ciudades cercanas (%.4f, %.4f)", lat, lon, exc_info=True)
            return []

    def detectar_ubicacion_ip(self) -> Ubicacion:
        """Detecta la ubicación geográfica real del usuario mediante GeoIP con doble fallback."""
        headers = {"User-Agent": "WeatherApp-Linux/1.0"}

        # Proveedor 1: ipapi.co
        try:
            response = sesion_http.get("https://ipapi.co/json/", headers=headers, timeout=4)
            if response.status_code == 200:
                data = response.json()
                ciudad = data.get("city") or data.get("region") or DEFAULT_CITY
                pais = data.get("country_name", "México")
                lat = float(data.get("latitude", DEFAULT_LATITUDE))
                lon = float(data.get("longitude", DEFAULT_LONGITUDE))
                tz = data.get("timezone", DEFAULT_TIMEZONE)
                region = data.get("region") or data.get("city")

                return Ubicacion(
                    ciudad=ciudad,
                    pais=pais,
                    latitud=lat,
                    longitud=lon,
                    timezone=tz,
                    admin1=region
                )
        except Exception:
            logger.warning("Fallo en proveedor de GeoIP ipapi.co", exc_info=True)

        # Proveedor 2: ipwho.is (ip-api.com no soporta HTTPS en su nivel gratuito)
        try:
            response = sesion_http.get("https://ipwho.is/", headers=headers, timeout=4)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return Ubicacion(
                        ciudad=data.get("city", DEFAULT_CITY),
                        pais=data.get("country", "México"),
                        latitud=float(data.get("latitude", DEFAULT_LATITUDE)),
                        longitud=float(data.get("longitude", DEFAULT_LONGITUDE)),
                        timezone=(data.get("timezone") or {}).get("id", DEFAULT_TIMEZONE),
                        admin1=data.get("region")
                    )
        except Exception:
            logger.warning("Fallo en proveedor de GeoIP ipwho.is", exc_info=True)

        # Fallback genérico neutral
        return Ubicacion(
            ciudad="Ciudad de México",
            pais="México",
            latitud=19.4326,
            longitud=-99.1332,
            timezone="America/Mexico_City"
        )
