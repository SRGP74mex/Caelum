import logging
import re
from typing import Dict, List, Optional

from config import (
    DEFAULT_CITY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEZONE,
    LANGUAGE,
    OPEN_METEO_GEOCODING_URL,
    USER_AGENT,
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
    def __init__(self, timeout: int = 4):
        self.timeout = timeout
        self._cache_busquedas: Dict[str, List[Ubicacion]] = {}

    def _normalizar_texto(self, consulta: str) -> str:
        """Reemplaza acrónimos y limpia separadores."""
        texto = consulta.strip()
        tokens = re.split(r'[,;\-\s]+', texto)
        tokens_normalizados = [ALIAS_CIUDADES.get(t.lower(), t) for t in tokens if t]
        return " ".join(tokens_normalizados)

    def buscar_ciudades(self, consulta: str, limite: int = 6, idioma: Optional[str] = None) -> List[Ubicacion]:
        """
        Búsqueda ultra-rápida y multi-estrategia con caché en memoria:
        1. Open-Meteo Geocoding con consulta procesada.
        2. Búsqueda por ciudad base si contiene comas (ej. "Zapopan, Jalisco").
        3. Fallback a Nominatim OpenStreetMap en caso necesario.
        """
        if not consulta or len(consulta.strip()) < 2:
            return []

        query_limpia = consulta.strip()
        query_key = f"{query_limpia.lower()}_{limite}_{idioma}"
        if query_key in self._cache_busquedas:
            return self._cache_busquedas[query_key]

        from src.servicios.i18n import obtener_idioma_actual
        idioma_req = idioma or obtener_idioma_actual()
        if idioma_req == "auto":
            idioma_req = "es"

        query_normalizada = self._normalizar_texto(query_limpia)

        # 1. Intentar Open-Meteo Geocoding directo
        resultados = self._buscar_open_meteo(query_normalizada, limite, idioma_req)
        if not resultados and query_normalizada != query_limpia:
            resultados = self._buscar_open_meteo(query_limpia, limite, idioma_req)

        # 2. Si la consulta tiene comas (ej: "Madrid, España"), buscar por el primer término
        if not resultados:
            partes = [p.strip() for p in re.split(r'[,]+', query_limpia) if p.strip()]
            if len(partes) > 1:
                resultados = self._buscar_open_meteo(partes[0], limite, idioma_req)

        # 3. Fallback a Nominatim solo si Open-Meteo no arrojó resultados
        if not resultados:
            resultados = self._buscar_nominatim(query_normalizada or query_limpia, limite)

        if resultados:
            self._cache_busquedas[query_key] = resultados

        return resultados

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
            logger.debug("Búsqueda Open-Meteo sin resultados para %r", nombre)
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
        headers = {"User-Agent": USER_AGENT}

        try:
            response = sesion_http.get(url, params=params, headers=headers, timeout=2.5)
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
            logger.debug("Fallo en búsqueda Nominatim para %r", query)
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
        headers = {"User-Agent": USER_AGENT}

        try:
            response = sesion_http.get(url, params=params, headers=headers, timeout=2.5)
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
            logger.debug("Fallo al obtener ciudades cercanas (%.4f, %.4f)", lat, lon)
            return []

    def detectar_ubicacion_ip(self) -> Ubicacion:
        """
        Detección multi-proveedor de GeoIP en cascada con fallback seguro:
        1. ipapi.co
        2. ipwho.is
        3. ip-api.com
        4. Fallback por defecto (Bogotá)
        """
        headers = {"User-Agent": USER_AGENT}

        # Proveedor 1: ipapi.co
        try:
            response = sesion_http.get("https://ipapi.co/json/", headers=headers, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if "latitude" in data and "longitude" in data and not data.get("error"):
                    return Ubicacion(
                        ciudad=data.get("city") or DEFAULT_CITY,
                        pais=data.get("country_name") or "Colombia",
                        latitud=float(data.get("latitude")),
                        longitud=float(data.get("longitude")),
                        timezone=data.get("timezone") or DEFAULT_TIMEZONE,
                        admin1=data.get("region")
                    )
        except Exception:
            logger.debug("Fallo en proveedor de GeoIP ipapi.co")

        # Proveedor 2: ipwho.is
        try:
            response = sesion_http.get("https://ipwho.is/", headers=headers, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("success", True) and "latitude" in data and "longitude" in data:
                    return Ubicacion(
                        ciudad=data.get("city") or DEFAULT_CITY,
                        pais=data.get("country") or "Colombia",
                        latitud=float(data.get("latitude")),
                        longitud=float(data.get("longitude")),
                        timezone=data.get("timezone", {}).get("id") or DEFAULT_TIMEZONE,
                        admin1=data.get("region")
                    )
        except Exception:
            logger.debug("Fallo en proveedor de GeoIP ipwho.is")

        # Proveedor 3: ip-api.com
        try:
            response = sesion_http.get("http://ip-api.com/json/", headers=headers, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return Ubicacion(
                        ciudad=data.get("city") or DEFAULT_CITY,
                        pais=data.get("country") or "Colombia",
                        latitud=float(data.get("lat")),
                        longitud=float(data.get("lon")),
                        timezone=data.get("timezone") or DEFAULT_TIMEZONE,
                        admin1=data.get("regionName")
                    )
        except Exception:
            logger.debug("Fallo en proveedor de GeoIP ip-api.com")

        logger.info("Usando ubicación por defecto de respaldo: %s", DEFAULT_CITY)
        return Ubicacion(
            ciudad=DEFAULT_CITY,
            pais="Colombia",
            latitud=DEFAULT_LATITUDE,
            longitud=DEFAULT_LONGITUDE,
            timezone=DEFAULT_TIMEZONE
        )
